"""Reglas del envío de sesiones (design de US-010, US-014 y EN-03, D4 a D6).

Toda regla y toda escritura de ``repositorio`` pasa por aquí; las vistas leen la petición,
llaman a estos servicios y responden.
"""

import logging
import re
import uuid
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import IntegrityError, transaction
from django.utils import timezone

from actividad.models import Operacion
from actividad.servicios import registrar
from catalogo.models import InstitucionArea
from institucion.servicios import secciones_docente, texto_seccion_corto
from repositorio.models import TAMANO_MAXIMO, TIPO_DOCX, TIPO_PDF, TITULO_MAXIMO, Sesion

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
_PRINCIPAL_DOCX = (
    b"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)
# Lo que puede lanzar un ZIP dañado, cifrado o con un método de compresión raro.
_ZIP_ROTO = (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError, OSError, KeyError)
_ZIP_ROTO += (RuntimeError, NotImplementedError, ValueError)


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


def _es_docx(archivo):
    """ZIP con ``word/document.xml`` y ``[Content_Types].xml`` que declara un .docx.

    Solo se leen el índice del ZIP y los primeros 64 KB de ``[Content_Types].xml``.
    """
    archivo.seek(0)
    try:
        with zipfile.ZipFile(archivo) as paquete:
            nombres = set(paquete.namelist())
            if "word/document.xml" not in nombres or "[Content_Types].xml" not in nombres:
                return False
            with paquete.open("[Content_Types].xml") as tipos:
                return _PRINCIPAL_DOCX in tipos.read(TIPOS_MAXIMO)
    except _ZIP_ROTO:
        return False


# Extensión → (tipo, cómo se reconoce por su contenido).
_TIPOS = {".pdf": (TIPO_PDF, _es_pdf), ".docx": (TIPO_DOCX, _es_docx)}


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


def _guardar(usuario, id_sesion, limpios, valido, archivo):
    """La fila, su entrada y el archivo en una transacción; nada si algo falla (D4, pasos 2 y 3).

    La fila va primero: un envío simultáneo con el mismo ``id`` queda esperando en la PK y nunca
    llega a escribir el archivo (D5).
    """
    clave = f"sesiones/{id_sesion}{valido.extension}"
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
        if guardado is not None:
            try:
                almacen.delete(guardado)
            except Exception:
                # Se conserva el error original; el objeto queda para borrarlo a mano.
                logger.exception("No se pudo borrar el archivo de una sesión que no se guardó.")
        raise
    return sesion


def enviar_sesion(usuario, datos, archivo):
    """Guarda la sesión que envía la docente ``usuario`` y devuelve la ``Sesion`` (D4, D5).

    ``datos`` es lo que manda el formulario (``id``, ``grado``, ``area``, ``titulo``,
    ``proposito``, ``compartir`` y ``acepta_terminos``) y ``archivo`` el archivo subido.

    Con un dato inválido, ``ValidationError`` con un mensaje por campo y nada escrito. Si la
    sesión de ese ``id`` ya es de la docente, la devuelve sin escribir (un reintento). Si el
    almacenamiento o la base fallan, se lanza su error sin dejar sesión, entrada ni archivo.
    """
    id_sesion = _uuid(_texto(datos, "id"))
    if id_sesion is None:
        raise _general()
    previa = _sesion_previa(usuario, id_sesion)
    if previa is not None:
        return previa

    limpios, valido = _validar(usuario, datos, archivo)
    try:
        return _guardar(usuario, id_sesion, limpios, valido, archivo)
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

# Cómo se nombra el tipo en el resumen («PDF · 1,2 MB», boceto).
_TIPO_CORTO = {TIPO_PDF: "PDF", TIPO_DOCX: "Word"}


def resumen(sesion):
    """Lo que muestra el Mensaje de éxito de ``sesion``: grado y tipo en palabras.

    El tamaño lo da formato la plantilla (``filesizeformat``, en el formato de es-pe).
    """
    return {
        "sesion": sesion,
        "grado": dict(GRADOS)[sesion.grado],
        "tipo": _TIPO_CORTO[sesion.tipo_mime],
    }
