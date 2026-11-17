"""Reglas del envío de sesiones (design de US-010, US-014 y EN-03, D4 a D6).

Toda regla y toda escritura de ``repositorio`` pasa por aquí; las vistas leen la petición,
llaman a estos servicios y responden.
"""

import io
import logging
import re
import secrets
import time
import uuid
import zipfile
import zlib
from dataclasses import dataclass
from datetime import timedelta
from pathlib import PurePosixPath
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.functions import Left
from django.urls import reverse
from django.utils import timezone
from django.utils.http import content_disposition_header
from storages.backends.s3 import S3Storage

from actividad.models import Operacion
from actividad.servicios import registrar
from catalogo.models import InstitucionArea
from institucion.servicios import secciones_docente, texto_seccion_corto
from repositorio.models import (
    TAMANO_MAXIMO,
    TIPO_DOCX,
    TIPO_PDF,
    TITULO_MAXIMO,
    Sesion,
    SesionVista,
)
from repositorio.texto import extraer_texto, normalizar

logger = logging.getLogger(__name__)

# Mensajes del campo archivo (boceto, sesiones.js).
FALTA_ARCHIVO = "Elige un archivo PDF o Word (.docx)."
NO_ES_PDF_NI_DOCX = "Este archivo no es PDF ni Word (.docx). Elige otro archivo."
ARCHIVO_GRANDE = "El archivo supera los 4 MB. Elige uno más pequeño."

NOMBRE_MAXIMO = 255
# De [Content_Types].xml solo se leen estos bytes: basta para un .docx real y acota un ZIP
# que se infla al descomprimir.
TIPOS_MAXIMO = 64 * 1024
# Tipo de la parte principal de un .docx; un .docm declara otro (macroEnabled) y no pasa.
_PRINCIPAL_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
_NS_TIPOS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
# Lo que puede lanzar un ZIP dañado, cifrado o con un método de compresión raro.
_ZIP_ROTO = (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError, OSError, KeyError)
_ZIP_ROTO += (RuntimeError, NotImplementedError, ValueError, ElementTree.ParseError)


class _SinDoctype(ElementTree.TreeBuilder):
    """Corta la lectura si hay ``<!DOCTYPE>``: un ``[Content_Types].xml`` real no lo trae y así
    no se expanden entidades."""

    def doctype(self, name, pubid, system):
        raise ValueError("[Content_Types].xml con DOCTYPE")


@dataclass(frozen=True)
class ArchivoValido:
    """Lo que se sabe de un archivo aceptado: el tipo sale del contenido, nunca del navegador."""

    tipo_mime: str
    extension: str
    nombre: str
    tamano: int


def nombre_limpio(nombre):
    """El nombre original sin rutas (de Windows o no), recortado a 255 con su extensión."""
    nombre = re.split(r"[\\/]", nombre or "")[-1].strip()
    if len(nombre) > NOMBRE_MAXIMO:
        extension = PurePosixPath(nombre).suffix[:NOMBRE_MAXIMO]
        nombre = nombre[: NOMBRE_MAXIMO - len(extension)] + extension
    return nombre


def _es_pdf(archivo):
    archivo.seek(0)
    return archivo.read(5) == b"%PDF-"


def _declara_docx(contenido):
    """``True`` si ``[Content_Types].xml`` da a ``/word/document.xml`` el tipo de un .docx.

    Se lee como XML: un comentario o un ``Default`` con ese texto no cuentan. Debe haber un solo
    ``Override`` de esa parte, con el tipo exacto, y ningún tipo ``macroEnabled``.
    """
    # Sin DOCTYPE no hay entidades ni DTD externos (billion laughs, XXE); entra 64 KB o menos.
    lector = ElementTree.XMLParser(target=_SinDoctype())  # noqa: S314
    lector.feed(contenido)
    raiz = lector.close()
    if raiz.tag != f"{_NS_TIPOS}Types":
        return False
    tipos = [hijo.get("ContentType", "") for hijo in raiz]
    if any("macroenabled" in tipo.lower() for tipo in tipos):
        return False
    principal = [
        hijo.get("ContentType")
        for hijo in raiz.iter(f"{_NS_TIPOS}Override")
        if hijo.get("PartName", "").lower() == "/word/document.xml"
    ]
    return principal == [_PRINCIPAL_DOCX]


def _es_docx(archivo):
    """ZIP con ``word/document.xml``, sin ``word/vbaProject.bin``, que declara un .docx (D6).

    Solo se leen el índice del ZIP y los primeros 64 KB de ``[Content_Types].xml``; si no cabe,
    el XML queda incompleto y se rechaza.
    """
    archivo.seek(0)
    try:
        with zipfile.ZipFile(archivo) as paquete:
            nombres = {nombre.lower() for nombre in paquete.namelist()}
            if not {"word/document.xml", "[content_types].xml"} <= nombres:
                return False
            if "word/vbaproject.bin" in nombres:
                return False
            with paquete.open("[Content_Types].xml") as tipos:
                return _declara_docx(tipos.read(TIPOS_MAXIMO))
    except _ZIP_ROTO:
        return False


# Extensión → (tipo, cómo se reconoce por su contenido).
_TIPOS = {".pdf": (TIPO_PDF, _es_pdf), ".docx": (TIPO_DOCX, _es_docx)}
# Cómo se nombra el tipo en el resumen («PDF · 1,2 MB», boceto) y en el log.
_TIPO_CORTO = {TIPO_PDF: "PDF", TIPO_DOCX: "Word"}


def validar_archivo(archivo):
    """``ArchivoValido`` si ``archivo`` es un PDF o un .docx de 1 byte a 4 MB (D6).

    La extensión y el contenido deben coincidir. Si no, ``ValidationError`` con el mensaje del
    campo. El archivo queda al principio para guardarlo después.
    """
    if archivo is None:
        raise ValidationError(FALTA_ARCHIVO, code="falta")
    if archivo.size > TAMANO_MAXIMO:
        raise ValidationError(ARCHIVO_GRANDE, code="grande")

    nombre = nombre_limpio(archivo.name)
    extension = PurePosixPath(nombre).suffix.lower()
    tipo, reconocer = _TIPOS.get(extension, (None, None))
    try:
        valido = archivo.size > 0 and reconocer is not None and reconocer(archivo)
    finally:
        archivo.seek(0)
    if not valido:
        raise ValidationError(NO_ES_PDF_NI_DOCX, code="tipo")
    return ArchivoValido(tipo_mime=tipo, extension=extension, nombre=nombre, tamano=archivo.size)


# --- Envío (D4, D5) -------------------------------------------------------------------------

PROPOSITO_MAXIMO = 1000
GRADOS = [(grado, f"{grado}.º grado") for grado in range(1, 7)]

# Mensajes de los campos (boceto; los que faltan siguen su forma).
FALTA_GRADO = "Falta indicar el grado."
GRADO_FUERA = "Elige un grado de la lista."
FALTA_AREA = "Falta indicar el área."
AREA_AJENA = "Elige un área de la lista."
FALTA_TITULO = "Falta indicar el título."
TITULO_LARGO = f"El título puede tener hasta {TITULO_MAXIMO} caracteres."
PROPOSITO_LARGO = f"El propósito puede tener hasta {PROPOSITO_MAXIMO} caracteres."
SIN_TERMINOS = "Para compartirla en el repositorio debes aceptar los términos."
# Un ``id`` mal formado o de otra autora: no lo provoca la pantalla (D5).
ERROR_GENERAL = "No se pudo enviar. Recarga la página e intenta de nuevo."

# Lo que manda una casilla marcada (``on``) o el script (``1``, ``true``).
_SI = {"on", "1", "true"}
# Tope de un id numérico: evita que un número enorme llegue a la base.
_ID_MAXIMO = 2**31


def casilla_marcada(valor):
    """``True`` si una casilla llegó marcada (``on``, ``1`` o ``true``)."""
    return (valor or "").strip().lower() in _SI


def _texto(datos, campo):
    return (datos.get(campo) or "").strip()


def _entero(valor):
    """El entero de ``valor`` si son solo dígitos ASCII y cabe en la base; si no, ``None``."""
    if not valor.isascii() or not valor.isdecimal():
        return None
    numero = int(valor)
    return numero if numero < _ID_MAXIMO else None


def _uuid(valor):
    try:
        return uuid.UUID(valor)
    except ValueError:
        return None


def _general():
    return ValidationError({"general": ERROR_GENERAL})


def _sesion_previa(usuario, id_sesion):
    """La sesión ya guardada con ese ``id`` si es de ``usuario``; error general si es de otra."""
    previa = Sesion.objects.filter(pk=id_sesion).first()
    if previa is not None and previa.autor_id != usuario.pk:
        raise _general()
    return previa


@dataclass(frozen=True)
class _Datos:
    grado: int
    area: object
    titulo: str
    proposito: str
    compartida: bool


def _validar_grado(datos, errores):
    texto = _texto(datos, "grado")
    if not texto:
        errores["grado"] = FALTA_GRADO
        return None
    grado = _entero(texto)
    if grado is None or not 1 <= grado <= 6:
        errores["grado"] = GRADO_FUERA
        return None
    return grado


def _validar_area(usuario, datos, errores):
    """El área si la institución de ``usuario`` la trabaja (RN-007)."""
    texto = _texto(datos, "area")
    if not texto:
        errores["area"] = FALTA_AREA
        return None
    area_id = _entero(texto)
    fila = None
    if area_id is not None:
        fila = (
            InstitucionArea.objects.filter(
                institucion_id=usuario.institucion_id, area_id=area_id, se_trabaja=True
            )
            .select_related("area")
            .first()
        )
    if fila is None:
        errores["area"] = AREA_AJENA
        return None
    return fila.area


def _validar(usuario, datos, archivo):
    """``(_Datos, ArchivoValido)`` o ``ValidationError`` con un mensaje por campo (D4, paso 1)."""
    errores = {}
    grado = _validar_grado(datos, errores)
    area = _validar_area(usuario, datos, errores)

    titulo = _texto(datos, "titulo")
    if not titulo:
        errores["titulo"] = FALTA_TITULO
    elif len(titulo) > TITULO_MAXIMO:
        errores["titulo"] = TITULO_LARGO

    proposito = _texto(datos, "proposito")
    if len(proposito) > PROPOSITO_MAXIMO:
        errores["proposito"] = PROPOSITO_LARGO

    compartida = _texto(datos, "compartir").lower() in _SI
    if compartida and _texto(datos, "acepta_terminos").lower() not in _SI:
        errores["compartir"] = SIN_TERMINOS

    valido = None
    try:
        valido = validar_archivo(archivo)
    except ValidationError as error:
        errores["archivo"] = error.messages[0]

    if errores:
        raise ValidationError(errores)
    return _Datos(grado, area, titulo, proposito, compartida), valido


def texto_de_busqueda(titulo, proposito, texto):
    """Lo que recorre la búsqueda de una sesión: título, propósito y texto, normalizados."""
    return normalizar(f"{titulo} {proposito} {texto}")


def _transcribir(archivo, tipo_mime):
    """El texto de ``archivo`` o ``""``; nunca detiene el envío (design de US-011, D3).

    Corre antes de la transacción. Deja en el log cuánto tardó, con el tipo y el largo del
    texto: ni el título ni el nombre del archivo.
    """
    inicio = time.perf_counter()
    try:
        texto = extraer_texto(archivo, tipo_mime)
    except Exception as error:
        # ``extraer_texto`` no lanza; si un día lo hace, la sesión se envía sin texto.
        logger.warning("La extracción de texto falló: %s", type(error).__name__)
        texto = ""
    finally:
        archivo.seek(0)
    logger.info(
        "Extracción de texto: %d ms, %s, %d caracteres.",
        (time.perf_counter() - inicio) * 1000,
        _TIPO_CORTO[tipo_mime],
        len(texto),
    )
    return texto


def _guardar(usuario, id_sesion, limpios, valido, archivo, texto):
    """La fila, su entrada y el archivo en una transacción; nada si algo falla (D4, pasos 2 y 3).

    La fila va primero: un envío simultáneo con el mismo ``id`` queda esperando en la PK y nunca
    llega a escribir el archivo (D5). La clave es de este intento (``<id>-<token>``) y se conoce
    antes de escribir: si algo falla se borra siempre, aunque ``save`` haya lanzado después de
    escribir, y nunca toca el archivo de otro intento con el mismo ``id`` que sí confirmó.
    """
    clave = f"sesiones/{id_sesion}-{secrets.token_hex(8)}{valido.extension}"
    almacen = storages["sesiones"]
    guardado = None
    try:
        with transaction.atomic():
            sesion = Sesion.objects.create(
                id=id_sesion,
                institucion_id=usuario.institucion_id,
                autor=usuario,
                subido_por=usuario,
                grado=limpios.grado,
                area=limpios.area,
                titulo=limpios.titulo,
                proposito=limpios.proposito,
                origen=Sesion.Origen.PROPIA,
                estado=Sesion.Estado.ENVIADA,
                compartida=limpios.compartida,
                terminos_aceptados_en=timezone.now() if limpios.compartida else None,
                archivo_clave=clave,
                archivo_nombre=valido.nombre,
                tipo_mime=valido.tipo_mime,
                tamano_bytes=valido.tamano,
                texto=texto,
                texto_busqueda=texto_de_busqueda(limpios.titulo, limpios.proposito, texto),
            )
            registrar(
                usuario,
                Operacion.SESION_ENVIADA,
                entidad=Sesion._meta.db_table,
                entidad_id=sesion.pk,
                detalle={"compartida": limpios.compartida},
            )
            guardado = almacen.save(clave, archivo)
            if guardado != clave:
                raise RuntimeError("El almacenamiento guardó el archivo con otra clave.")
    except BaseException:
        for escrita in dict.fromkeys([clave, guardado]):
            if escrita is None:
                continue
            try:
                almacen.delete(escrita)
            except Exception:
                # Se conserva el error original; el objeto queda para borrarlo a mano.
                logger.exception("No se pudo borrar %s, de una sesión que no se guardó.", escrita)
        raise
    return sesion


def enviar_sesion(usuario, datos, archivo):
    """Guarda la sesión que envía la docente ``usuario`` y devuelve la ``Sesion`` (D4, D5).

    ``datos`` es lo que manda el formulario (``id``, ``grado``, ``area``, ``titulo``,
    ``proposito``, ``compartir`` y ``acepta_terminos``) y ``archivo`` el archivo subido.

    Con un dato inválido, ``ValidationError`` con un mensaje por campo y nada escrito. Si la
    sesión de ese ``id`` ya es de la docente, la devuelve sin escribir (un reintento). Si el
    almacenamiento o la base fallan, se lanza su error sin dejar sesión, entrada ni archivo.

    El texto del archivo se extrae después de validar y antes de la transacción; si no se puede
    leer, la sesión se envía igual, sin texto (design de US-011, D3).
    """
    id_sesion = _uuid(_texto(datos, "id"))
    if id_sesion is None:
        raise _general()
    previa = _sesion_previa(usuario, id_sesion)
    if previa is not None:
        return previa

    limpios, valido = _validar(usuario, datos, archivo)
    texto = _transcribir(archivo, valido.tipo_mime)
    try:
        return _guardar(usuario, id_sesion, limpios, valido, archivo, texto)
    except IntegrityError:
        # Otro envío con el mismo id llegó primero (D5): su éxito es el de este.
        previa = _sesion_previa(usuario, id_sesion)
        if previa is None:
            raise
        return previa


# --- Formulario (D9) ------------------------------------------------------------------------


def datos_del_formulario(usuario):
    """Grados, áreas de la institución (``se_trabaja``, orden SIAGIE) y grado por defecto.

    Con una sola sección en el año ABIERTO, el grado es el suyo; con varias o ninguna, ninguno.
    """
    secciones = list(secciones_docente(usuario))
    if len(secciones) == 1:
        grado = secciones[0].grado
        ayuda = f"Grado de tu sección: {texto_seccion_corto(secciones[0])}. Puedes cambiarlo."
    else:
        grado = None
        ayuda = "Elige el grado de esta sesión."
    areas = [
        fila.area
        for fila in InstitucionArea.objects.filter(
            institucion_id=usuario.institucion_id, se_trabaja=True
        )
        .select_related("area")
        .order_by("area__orden", "area__pk")
    ]
    return {"grados": GRADOS, "grado": grado, "ayuda_grado": ayuda, "areas": areas}


# --- Resumen del envío (D7) -----------------------------------------------------------------


def resumen(sesion):
    """Lo que muestra el Mensaje de éxito de ``sesion``: grado y tipo en palabras.

    El tamaño lo da formato la plantilla (``filesizeformat``, en el formato de es-pe).
    """
    return {
        "sesion": sesion,
        "grado": dict(GRADOS)[sesion.grado],
        "tipo": _TIPO_CORTO[sesion.tipo_mime],
    }


# --- Sesiones anteriores (design de US-011, D3) ----------------------------------------------


@dataclass(frozen=True)
class Transcritas:
    """Lo que hizo ``transcribir_pendientes``."""

    con_texto: int
    sin_texto: int
    sin_archivo: int

    def texto(self):
        total = self.con_texto + self.sin_texto + self.sin_archivo
        return (
            f"Sesiones sin texto: {total}. Con texto ahora: {self.con_texto}. "
            f"Siguen sin texto: {self.sin_texto}. No se pudo abrir su archivo: {self.sin_archivo}."
        )


def transcribir_pendientes():
    """Llena el texto de las sesiones que no lo tienen, desde su archivo del almacenamiento.

    Para las sesiones enviadas antes de US-011; lo corre el comando ``extraer_textos``. No toca
    las que ya tienen texto, así que repetirlo no cambia nada. Un archivo que no se puede abrir
    queda en el log con su clave (nunca el título) y no detiene a las demás. No es una acción de
    una docente: no deja entrada de actividad ni cambia ``actualizado_en``.
    """
    almacen = storages["sesiones"]
    pendientes = list(
        Sesion.objects.filter(texto="")
        .order_by("creado_en", "pk")
        .values_list("pk", "archivo_clave", "tipo_mime", "titulo", "proposito", "texto_busqueda")
    )
    con_texto = sin_texto = sin_archivo = 0
    for pk, clave, tipo_mime, titulo, proposito, busqueda in pendientes:
        if not busqueda:
            # Nació con el código anterior, después de la migración 0002: sin esto, ni el título
            # ni el propósito la encuentran aunque el archivo no dé texto.
            Sesion.objects.filter(pk=pk, texto_busqueda="").update(
                texto_busqueda=texto_de_busqueda(titulo, proposito, "")
            )
        try:
            with almacen.open(clave) as guardado:
                contenido = io.BytesIO(guardado.read(TAMANO_MAXIMO + 1))
        except Exception as error:
            logger.warning("No se pudo abrir %s: %s", clave, type(error).__name__)
            sin_archivo += 1
            continue
        texto = extraer_texto(contenido, tipo_mime)
        if not texto:
            sin_texto += 1
            continue
        # Solo si sigue sin texto: no pisa lo que otra corrida guardó mientras tanto.
        Sesion.objects.filter(pk=pk, texto="").update(
            texto=texto, texto_busqueda=texto_de_busqueda(titulo, proposito, texto)
        )
        con_texto += 1
    return Transcritas(con_texto=con_texto, sin_texto=sin_texto, sin_archivo=sin_archivo)


# --- Visibilidad y consultas (design de US-011, D4 y D5) -------------------------------------

LIMA = ZoneInfo("America/Lima")
POR_PAGINA = 20
# Lo que se lee del texto para la página dibujada de la tarjeta.
INICIO_TEXTO = 600
BUSQUEDA_MAXIMA = 100
PALABRAS_MAXIMAS = 8
# Tope de ``?pagina=``: evita un desplazamiento enorme en la base.
_PAGINA_MAXIMA = 10_000
_DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def sesion_visible(usuario, id_sesion, con_texto=True):
    """La sesión ``id_sesion`` si ``usuario`` puede verla; si no, ``None`` (D5).

    La ve su autora, compartida o no, y cualquier cuenta de la misma institución si está
    compartida. Es la única puerta de la página, la descarga, la vista y las escrituras: lo no
    visible es igual a lo inexistente. Un ``id`` que no es UUID tampoco es visible.
    """
    if not isinstance(id_sesion, uuid.UUID):
        id_sesion = _uuid(str(id_sesion or ""))
        if id_sesion is None:
            return None
    consulta = Sesion.objects.all()
    if not con_texto:
        consulta = consulta.defer("texto", "texto_busqueda")
    return (
        consulta.filter(pk=id_sesion)
        .filter(Q(autor_id=usuario.pk) | Q(compartida=True, institucion_id=usuario.institucion_id))
        .select_related("area", "autor")
        .first()
    )


@dataclass(frozen=True)
class Pagina:
    """Una página de tarjetas: las sesiones en orden y si hay más después."""

    sesiones: list
    hay_mas: bool
    pagina: int
    # Solo del repositorio: total con los filtros y los filtros que sí se aplicaron.
    total: int | None = None
    q: str = ""
    grado: int | None = None
    area: object = None

    @property
    def grupos(self):
        """Las sesiones agrupadas por día de envío en hora de Lima: «Hoy», «Ayer», «lun 2 nov»."""
        hoy = timezone.localtime(timezone.now(), LIMA).date()
        grupos = []
        for sesion in self.sesiones:
            dia = timezone.localtime(sesion.creado_en, LIMA).date()
            etiqueta = _etiqueta_dia(dia, hoy)
            if grupos and grupos[-1][0] == etiqueta:
                grupos[-1][1].append(sesion)
            else:
                grupos.append((etiqueta, [sesion]))
        return grupos


def _etiqueta_dia(dia, hoy):
    if dia == hoy:
        return "Hoy"
    if dia == hoy - timedelta(days=1):
        return "Ayer"
    return f"{_DIAS[dia.weekday()]} {dia.day} {_MESES[dia.month - 1]}"


def _numero_de_pagina(valor):
    if isinstance(valor, int):
        numero = valor
    else:
        numero = _entero((valor or "").strip())
    if numero is None or not 1 <= numero <= _PAGINA_MAXIMA:
        return 1
    return numero


def _tarjetas(consulta):
    """Lo que necesita una tarjeta, sin el texto completo ni el de búsqueda (D5)."""
    return (
        consulta.select_related("area", "autor")
        .defer("texto", "texto_busqueda")
        .annotate(inicio_texto=Left("texto", INICIO_TEXTO))
        .order_by("-creado_en", "pk")
    )


def _paginar(consulta, pagina):
    numero = _numero_de_pagina(pagina)
    inicio = (numero - 1) * POR_PAGINA
    filas = list(consulta[inicio : inicio + POR_PAGINA + 1])
    return filas[:POR_PAGINA], len(filas) > POR_PAGINA, numero


def mis_sesiones(usuario, pagina=1):
    """Las sesiones que envió ``usuario``, compartidas o no, con cuántas colegas las vieron."""
    consulta = _tarjetas(Sesion.objects.filter(autor_id=usuario.pk)).annotate(
        vistas_total=Count("vistas")
    )
    sesiones, hay_mas, numero = _paginar(consulta, pagina)
    return Pagina(sesiones=sesiones, hay_mas=hay_mas, pagina=numero)


def _compartidas(usuario):
    """Las compartidas de la institución de ``usuario``: nunca sale de la petición."""
    return Sesion.objects.filter(institucion_id=usuario.institucion_id, compartida=True)


def limpiar_busqueda(q):
    """La búsqueda tal como se muestra: sin espacios en los bordes y hasta 100 caracteres."""
    return (q or "").strip()[:BUSQUEDA_MAXIMA].strip()


def _con_palabras(consulta, q):
    """Cada palabra (hasta 8) debe estar en ``texto_busqueda``; Django escapa ``%`` y ``_``."""
    for palabra in normalizar(limpiar_busqueda(q)).split()[:PALABRAS_MAXIMAS]:
        consulta = consulta.filter(texto_busqueda__contains=palabra)
    return consulta


def _grado_valido(valor):
    """El grado de 1 a 6, o ``None``: un valor inválido llega por la dirección y se ignora."""
    grado = _entero((valor or "").strip()) if isinstance(valor, str) else valor
    return grado if isinstance(grado, int) and 1 <= grado <= 6 else None


def _areas_trabajadas(usuario):
    return InstitucionArea.objects.filter(
        institucion_id=usuario.institucion_id, se_trabaja=True
    ).select_related("area")


def _area_valida(usuario, valor):
    """El área si la institución la trabaja; si no, ``None`` (se ignora)."""
    area_id = _entero((valor or "").strip()) if isinstance(valor, str) else None
    if area_id is None:
        return None
    fila = _areas_trabajadas(usuario).filter(area_id=area_id).first()
    return fila.area if fila else None


def buscar_repositorio(usuario, q="", grado="", area="", pagina=1):
    """Las compartidas de la institución que cumplen la búsqueda, el grado y el área (D4, D5)."""
    grado_valido = _grado_valido(grado)
    area_valida = _area_valida(usuario, area)
    consulta = _con_palabras(_compartidas(usuario), q)
    if grado_valido is not None:
        consulta = consulta.filter(grado=grado_valido)
    if area_valida is not None:
        consulta = consulta.filter(area=area_valida)
    total = consulta.count()
    sesiones, hay_mas, numero = _paginar(_tarjetas(consulta), pagina)
    return Pagina(
        sesiones=sesiones,
        hay_mas=hay_mas,
        pagina=numero,
        total=total,
        q=limpiar_busqueda(q),
        grado=grado_valido,
        area=area_valida,
    )


@dataclass(frozen=True)
class ConteosPorArea:
    """«Todas las áreas» y cada área que la institución trabaja, en orden SIAGIE, con su total."""

    total: int
    areas: list


def conteos_por_area(usuario, q="", grado=""):
    """Cuántas compartidas hay por área con la búsqueda y el grado vigentes (D5)."""
    consulta = _con_palabras(_compartidas(usuario), q)
    grado_valido = _grado_valido(grado)
    if grado_valido is not None:
        consulta = consulta.filter(grado=grado_valido)
    por_area = dict(
        consulta.order_by().values("area_id").annotate(n=Count("pk")).values_list("area_id", "n")
    )
    areas = [
        (fila.area, por_area.get(fila.area_id, 0))
        for fila in _areas_trabajadas(usuario).order_by("area__orden", "area__pk")
    ]
    return ConteosPorArea(total=sum(por_area.values()), areas=areas)


def contadores(usuario):
    """Los totales de las pestañas, sin filtros (D5)."""
    return {
        "mis_sesiones": Sesion.objects.filter(autor_id=usuario.pk).count(),
        "repositorio": _compartidas(usuario).count(),
    }


# --- Vistas y entrega del archivo (design de US-011, D6 y D7) --------------------------------

# Vida del enlace firmado de R2 (decisión 10).
ENLACE_SEGUNDOS = 60
# Modo → si el navegador debe guardarlo (descarga) o mostrarlo (vista del PDF).
_MODOS = {"descargar": True, "ver": False}


class SesionNoDisponible(Exception):
    """La sesión no existe o quien la pide no puede verla: se responde igual en los dos casos."""


def registrar_vista(usuario, sesion):
    """Cuenta la primera vez que una colega abre la página de ``sesion`` (D6).

    Devuelve ``True`` solo si es esa primera vez: entonces crea su ``SesionVista`` y deja
    SESION_VISTA, juntas. La autora no cuenta. La página leyó ``sesion`` antes: aquí se vuelve a
    comprobar, con la fila bloqueada, que sigue compartida en su institución; si la autora la
    eliminó o la dejó de compartir mientras tanto, ``SesionNoDisponible`` y nada se cuenta.
    """
    if sesion.autor_id == usuario.pk:
        return False
    with transaction.atomic():
        vigente = (
            Sesion.objects.select_for_update(no_key=True)
            .only("pk")
            .filter(pk=sesion.pk, compartida=True, institucion_id=usuario.institucion_id)
            .exists()
        )
        if not vigente:
            raise SesionNoDisponible
        _, creada = SesionVista.objects.get_or_create(sesion=sesion, usuario=usuario)
        if creada:
            registrar(
                usuario,
                Operacion.SESION_VISTA,
                entidad=Sesion._meta.db_table,
                entidad_id=sesion.pk,
            )
    return creada


@dataclass(frozen=True)
class Entrega:
    """Cómo responder una descarga: un enlace firmado (``url``) o el archivo abierto."""

    url: str | None
    archivo: object
    tipo_mime: str
    disposicion: str


def entregar_archivo(usuario, id_sesion, modo):
    """El archivo de la sesión para ``modo`` («descargar» o «ver»), con su SESION_DESCARGADA.

    El permiso se revisa en cada petición (``sesion_visible``). «Ver» solo existe para el PDF.
    Si no está disponible, ``SesionNoDisponible`` sin entrada. Con ``S3Storage`` devuelve un
    enlace firmado de 60 s que fija el nombre original y el modo; con otro almacén, el archivo
    abierto. Si no se puede firmar ni abrir, no queda la entrada (D7).
    """
    if modo not in _MODOS:
        raise ValueError(f"Modo de entrega desconocido: {modo!r}")
    sesion = sesion_visible(usuario, id_sesion, con_texto=False)
    if sesion is None or (modo == "ver" and sesion.tipo_mime != TIPO_PDF):
        raise SesionNoDisponible
    disposicion = content_disposition_header(_MODOS[modo], sesion.archivo_nombre)
    almacen = storages["sesiones"]
    with transaction.atomic():
        registrar(
            usuario,
            Operacion.SESION_DESCARGADA,
            entidad=Sesion._meta.db_table,
            entidad_id=sesion.pk,
            detalle={"modo": modo, "propia": sesion.autor_id == usuario.pk},
        )
        if isinstance(almacen, S3Storage):
            url = almacen.url(
                sesion.archivo_clave,
                parameters={
                    "ResponseContentDisposition": disposicion,
                    "ResponseContentType": sesion.tipo_mime,
                    # La que trae el archivo es la respuesta de R2, no la del aplicativo.
                    "ResponseCacheControl": "no-store",
                },
                expire=ENLACE_SEGUNDOS,
            )
            return Entrega(url, None, sesion.tipo_mime, disposicion)
        archivo = almacen.open(sesion.archivo_clave, "rb")
    return Entrega(None, archivo, sesion.tipo_mime, disposicion)


# --- Escrituras de la autora (design de US-011, D8) ------------------------------------------

# Motivos del intento sin permiso sobre una sesión. Solo van al registro: la respuesta de una
# no visible es la misma que la de una inexistente.
SESION_AJENA = "sesion_ajena"
SESION_NO_VISIBLE = "sesion_no_visible"


class SoloLaAutora(Exception):
    """Otra docente pidió eliminar, compartir o dejar de compartir una sesión que sí puede ver."""

    def __init__(self):
        super().__init__("Solo el autor puede eliminar esta sesión")


def _intento_sobre_sesion(usuario, id_sesion, ruta, motivo):
    """Una entrada INTENTO_SIN_PERMISO por la sesión ``id_sesion`` (spec registro-actividad).

    ``ruta`` es ``request.path``: solo el UUID, sin título ni otro dato de la sesión (RN-015).
    """
    registrar(
        usuario,
        Operacion.INTENTO_SIN_PERMISO,
        entidad=Sesion._meta.db_table,
        entidad_id=id_sesion,
        detalle={"ruta": ruta, "motivo": motivo},
    )


def _bloquear_de_la_autora(usuario, id_sesion, ruta):
    """La sesión de ``usuario`` con su fila bloqueada, o el error que corresponde (D8).

    Debe llamarse dentro de una transacción. Si no es de ``usuario``: inexistente → ``None`` y
    ``SesionNoDisponible`` sin entrada; ajena no visible → INTENTO_SIN_PERMISO y
    ``SesionNoDisponible``; ajena visible (``sesion_visible``) → INTENTO_SIN_PERMISO y
    ``SoloLaAutora``. El error se devuelve, no se lanza: la entrada del intento debe confirmarse.
    """
    if not isinstance(id_sesion, uuid.UUID):
        id_sesion = _uuid(str(id_sesion or ""))
        if id_sesion is None:
            return None, SesionNoDisponible()
    sesion = (
        Sesion.objects.select_for_update()
        .defer("texto", "texto_busqueda")
        .filter(pk=id_sesion, autor_id=usuario.pk)
        .first()
    )
    if sesion is not None:
        return sesion, None
    if not Sesion.objects.filter(pk=id_sesion).exists():
        return None, SesionNoDisponible()
    if sesion_visible(usuario, id_sesion, con_texto=False) is not None:
        _intento_sobre_sesion(usuario, id_sesion, ruta, SESION_AJENA)
        return None, SoloLaAutora()
    _intento_sobre_sesion(usuario, id_sesion, ruta, SESION_NO_VISIBLE)
    return None, SesionNoDisponible()


def _borrar_archivo(clave):
    try:
        storages["sesiones"].delete(clave)
    except Exception:
        # La sesión ya no existe: el objeto queda huérfano en el bucket privado. Solo la clave
        # va al log, nunca el título ni la autora (deuda: comando de conciliación).
        logger.exception("No se pudo borrar %s, de una sesión eliminada.", clave)


def borrar_sesiones(consulta):
    """Borra las sesiones de ``consulta`` y, al confirmarse, sus archivos (D8, D11).

    Sus vistas caen por ``CASCADE``. Si la transacción no se confirma, los archivos siguen. Va
    dentro de una transacción; devuelve cuántas sesiones borró.
    """
    filas = list(consulta.values_list("pk", "archivo_clave"))
    Sesion.objects.filter(pk__in=[pk for pk, _ in filas]).delete()
    for _, clave in filas:
        transaction.on_commit(lambda clave=clave: _borrar_archivo(clave))
    return len(filas)


def eliminar_sesion(usuario, id_sesion, ruta):
    """Elimina la sesión de ``usuario`` y, al confirmarse, su archivo; deja SESION_ELIMINADA.

    ``SesionNoDisponible`` si no existe o no la ve; ``SoloLaAutora`` si la ve y es de otra (las
    dos ajenas dejan INTENTO_SIN_PERMISO). Eliminarla dos veces: la segunda no está disponible
    y no deja entrada.
    """
    with transaction.atomic():
        sesion, error = _bloquear_de_la_autora(usuario, id_sesion, ruta)
        if sesion is not None:
            borrar_sesiones(Sesion.objects.filter(pk=sesion.pk))
            registrar(
                usuario,
                Operacion.SESION_ELIMINADA,
                entidad=Sesion._meta.db_table,
                entidad_id=sesion.pk,
                detalle={"compartida": sesion.compartida},
            )
    if error is not None:
        raise error


def compartir_sesion(usuario, id_sesion, acepta, ruta):
    """Comparte la sesión de ``usuario`` con la fecha de esta aceptación (decisión 13).

    Sin ``acepta``, ``ValidationError`` con el mensaje de los términos y nada cambia. Si ya está
    compartida, la devuelve igual y sin entrada. Los mismos errores que ``eliminar_sesion``.
    """
    with transaction.atomic():
        sesion, error = _bloquear_de_la_autora(usuario, id_sesion, ruta)
        if sesion is not None:
            if not acepta:
                raise ValidationError(SIN_TERMINOS, code="terminos")
            if not sesion.compartida:
                sesion.compartida = True
                sesion.terminos_aceptados_en = timezone.now()
                sesion.save(update_fields=["compartida", "terminos_aceptados_en", "actualizado_en"])
                registrar(
                    usuario,
                    Operacion.SESION_COMPARTIDA,
                    entidad=Sesion._meta.db_table,
                    entidad_id=sesion.pk,
                )
    if error is not None:
        raise error
    return sesion


def dejar_de_compartir(usuario, id_sesion, ruta):
    """Saca del repositorio la sesión de ``usuario``; conserva la fecha de los términos.

    Si ya no estaba compartida, la devuelve igual y sin entrada. Los mismos errores que
    ``eliminar_sesion``.
    """
    with transaction.atomic():
        sesion, error = _bloquear_de_la_autora(usuario, id_sesion, ruta)
        if sesion is not None and sesion.compartida:
            sesion.compartida = False
            sesion.save(update_fields=["compartida", "actualizado_en"])
            registrar(
                usuario,
                Operacion.SESION_DESCOMPARTIDA,
                entidad=Sesion._meta.db_table,
                entidad_id=sesion.pk,
            )
    if error is not None:
        raise error
    return sesion


def datos_de_la_pagina(usuario, sesion):
    """Lo que muestra la página de ``sesion`` a ``usuario`` (D5, D10).

    Las migas llevan a «Mis sesiones» si es suya y al «Repositorio» si es de una colega. El
    total de colegas que la vieron solo se da a la autora.
    """
    propia = sesion.autor_id == usuario.pk
    if propia:
        miga = ("Mis sesiones", reverse("sesiones:inicio"))
    else:
        miga = ("Repositorio", reverse("sesiones:repositorio"))
    return {
        "sesion": sesion,
        "propia": propia,
        "miga": miga,
        "grado": dict(GRADOS)[sesion.grado],
        "vistas_total": sesion.vistas.count() if propia else None,
    }
