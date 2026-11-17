"""Sesiones de ejemplo de la demostración (spec datos-demostracion; design de US-011, D11).

Los archivos se arman en código con lo mínimo de cada formato real: un PDF con capa de texto,
un PDF sin texto (como una hoja escaneada) y un .docx. Todo el texto es ficticio (RN-018). Las
llama ``institucion.demo``: no pasan por ``enviar_sesion`` ni dejan SESION_ENVIADA, así que no
cuentan en los indicadores.
"""

import datetime
import io
import uuid
import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

from django.core.files.base import ContentFile
from django.core.files.storage import storages

from catalogo.models import InstitucionArea
from cuentas.models import Usuario
from repositorio import servicios
from repositorio.models import TIPO_DOCX, TIPO_PDF, Sesion, SesionVista
from repositorio.texto import extraer_texto

# --- Archivos -------------------------------------------------------------------------------


def _cadena_pdf(texto):
    """``texto`` como cadena literal de PDF en WinAnsi, con sus escapes."""
    crudo = texto.encode("cp1252")
    for signo in (b"\\", b"(", b")"):
        crudo = crudo.replace(signo, b"\\" + signo)
    return b"(" + crudo + b")"


def pdf_con_texto(paginas):
    """Un PDF con capa de texto: ``paginas`` es una lista de páginas, cada una con sus líneas.

    Una página sin líneas queda en blanco, como una hoja escaneada sin texto reconocido.
    """
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        None,  # el árbol de páginas, cuando se conocen sus números
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    hijas = []
    for lineas in paginas:
        dibujo = b"BT /F1 12 Tf 14 TL 72 720 Td "
        dibujo += b" ".join(_cadena_pdf(linea) + b" Tj T*" for linea in lineas) + b" ET"
        contenido = len(objetos) + 2
        hijas.append(len(objetos) + 1)
        objetos.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % contenido
        )
        objetos.append(b"<< /Length %d >>\nstream\n" % len(dibujo) + dibujo + b"\nendstream")
    objetos[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % numero for numero in hijas),
        len(hijas),
    )

    salida = io.BytesIO()
    salida.write(b"%PDF-1.4\n")
    posiciones = []
    for numero, objeto in enumerate(objetos, start=1):
        posiciones.append(salida.tell())
        salida.write(b"%d 0 obj\n" % numero + objeto + b"\nendobj\n")
    tabla = salida.tell()
    salida.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1))
    for posicion in posiciones:
        salida.write(b"%010d 00000 n \n" % posicion)
    salida.write(
        b"trailer << /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, tabla)
    )
    return salida.getvalue()


_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_TIPOS_DOCX = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/'
    'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)
# La relación que Word busca para abrir el documento principal.
_RELACIONES_DOCX = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)


def docx_con_texto(parrafos):
    """Un .docx que Word abre: un párrafo por cada texto de ``parrafos``."""
    cuerpo = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>'
        for texto in parrafos
    )
    documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_NS_W}"><w:body>{cuerpo}</w:body></w:document>'
    )
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr("[Content_Types].xml", _TIPOS_DOCX)
        paquete.writestr("_rels/.rels", _RELACIONES_DOCX)
        paquete.writestr("word/document.xml", documento)
    return salida.getvalue()


# --- Sesiones -------------------------------------------------------------------------------

PDF, WORD, ESCANEADO = "pdf", "word", "escaneado"
# Identificador estable de cada sesión de ejemplo: la misma carga da los mismos ``id``.
_ESPACIO_DEMO = uuid.UUID("6f1c2d0e-8a4b-4c7e-9d35-0b1e7a5c3f20")


@dataclass(frozen=True)
class Ejemplo:
    """Una sesión de ejemplo; ``area`` es la posición entre las áreas que trabaja la I.E."""

    cuenta: str
    grado: int
    area: int
    titulo: str
    proposito: str
    formato: str
    compartida: bool
    dias_atras: int
    lineas: tuple[str, ...] = ()


EJEMPLOS = (
    Ejemplo(
        "demounoa",
        1,
        0,
        "Leemos un cuento sobre la amistad",
        "Que reconozcan a los personajes y comenten qué hicieron por sus amigos.",
        PDF,
        True,
        1,
        (
            "Inicio: saludamos y recordamos qué es un amigo.",
            "Desarrollo: leemos el cuento del zorro y la tortuga en voz alta.",
            "Conversamos sobre los personajes y lo que sintieron.",
            "Cierre: dibujamos un momento del cuento y lo compartimos.",
        ),
    ),
    Ejemplo(
        "demounob",
        1,
        1,
        "Contamos y agrupamos semillas",
        "Que formen grupos de hasta diez y digan cuántos hay.",
        WORD,
        True,
        2,
        (
            "Materiales: semillas de maíz, habas y vasos de colores.",
            "Formamos grupos de cinco y de diez sobre la mesa.",
            "Registramos en la pizarra cuántas semillas tiene cada grupo.",
        ),
    ),
    Ejemplo(
        "demounoc",
        2,
        2,
        "Cuidamos las plantas del biohuerto",
        "",
        PDF,
        True,
        3,
        (
            "Observamos las plantas del biohuerto con una lupa.",
            "Anotamos cuánta agua necesita cada planta y cuándo regarla.",
            "Elaboramos un horario de riego para el aula.",
        ),
    ),
    Ejemplo(
        "demounod",
        2,
        0,
        "Escribimos una receta de mazamorra",
        "Que escriban los pasos de una receta en orden.",
        WORD,
        True,
        4,
        (
            "Leemos una receta modelo y señalamos sus partes.",
            "Ordenamos los pasos con tarjetas y conectores: primero, luego, finalmente.",
            "Cada equipo escribe su receta y la revisa con una lista de cotejo.",
        ),
    ),
    Ejemplo(
        "demodosa",
        3,
        1,
        "Medimos el aula con pasos y cuartas",
        "Que comparen medidas con unidades no convencionales.",
        PDF,
        True,
        5,
        (
            "Estimamos cuántos pasos mide el aula antes de medirla.",
            "Medimos el largo y el ancho con pasos, cuartas y pies.",
            "Comparamos resultados y conversamos por qué no coinciden.",
        ),
    ),
    Ejemplo(
        "demodosb",
        4,
        3,
        "Conocemos las danzas de nuestra región",
        "",
        ESCANEADO,
        True,
        6,
    ),
    Ejemplo(
        "demodosc",
        5,
        2,
        "Representamos el ciclo del agua",
        "Que expliquen con un esquema cómo circula el agua.",
        WORD,
        True,
        8,
        (
            "Recogemos saberes previos sobre la lluvia y los ríos.",
            "Hacemos un experimento con una olla, hielo y un plato.",
            "Dibujamos el esquema de evaporación, condensación y precipitación.",
        ),
    ),
    Ejemplo(
        "demodosd",
        6,
        1,
        "Resolvemos problemas con fracciones",
        "Que representen fracciones con material concreto.",
        PDF,
        True,
        9,
        (
            "Repartimos una tortilla de papel en partes iguales.",
            "Representamos medios, tercios y cuartos con tiras de colores.",
            "Resolvemos problemas de reparto en parejas y los explicamos.",
        ),
    ),
    Ejemplo(
        "demounoa",
        1,
        4,
        "Jugamos a lanzar y atrapar la pelota",
        "",
        WORD,
        False,
        10,
        (
            "Calentamiento con movimientos de brazos y piernas.",
            "Lanzamos y atrapamos la pelota en parejas a distintas distancias.",
            "Relajación y conversación sobre cómo nos sentimos.",
        ),
    ),
    Ejemplo(
        "demodosa",
        3,
        0,
        "Describimos a un animal de la sierra",
        "Que describan las características de un animal.",
        PDF,
        False,
        12,
        (
            "Observamos imágenes de la vicuña, la llama y el cóndor.",
            "Elegimos un animal y anotamos cómo es, dónde vive y qué come.",
            "Escribimos un texto descriptivo corto y lo leemos al grupo.",
        ),
    ),
)

_EXTENSION = {PDF: ".pdf", ESCANEADO: ".pdf", WORD: ".docx"}
_TIPO = {PDF: TIPO_PDF, ESCANEADO: TIPO_PDF, WORD: TIPO_DOCX}


def _contenido(ejemplo):
    if ejemplo.formato == WORD:
        return docx_con_texto(ejemplo.lineas)
    if ejemplo.formato == ESCANEADO:
        return pdf_con_texto([[]])
    return pdf_con_texto([ejemplo.lineas])


def id_de(ejemplo, indice):
    """El ``id`` estable de la sesión de ejemplo: de su cuenta y su posición (D11)."""
    return uuid.uuid5(_ESPACIO_DEMO, f"{ejemplo.cuenta}-{indice}")


def cargar_sesiones(institucion, hoy, zona, escritas):
    """Crea las sesiones de ejemplo que falten de las cuentas demo de ``institucion``.

    Las que ya existen se saltan: volver a cargar no duplica sesiones ni archivos. Cada clave
    escrita se agrega a ``escritas`` antes de guardar, para que quien llama borre los archivos si
    su transacción falla. ``creado_en`` va de 1 a 12 días antes de ``hoy``, a media mañana en
    ``zona``. Devuelve cuántas creó.
    """
    cuentas = {
        cuenta.username: cuenta
        for cuenta in Usuario.objects.filter(
            es_demo=True, rol=Usuario.Rol.DOCENTE, institucion=institucion
        )
    }
    areas = [
        fila.area
        for fila in InstitucionArea.objects.filter(institucion=institucion, se_trabaja=True)
        .select_related("area")
        .order_by("area__orden", "area__pk")
    ]
    if not areas:
        return 0
    almacen = storages["sesiones"]
    creadas = 0
    for indice, ejemplo in enumerate(EJEMPLOS):
        cuenta = cuentas.get(ejemplo.cuenta)
        id_sesion = id_de(ejemplo, indice)
        if cuenta is None or Sesion.objects.filter(pk=id_sesion).exists():
            continue
        contenido = _contenido(ejemplo)
        tipo = _TIPO[ejemplo.formato]
        texto = extraer_texto(io.BytesIO(contenido), tipo)
        clave = f"sesiones/{id_sesion}-demo{_EXTENSION[ejemplo.formato]}"
        creado = datetime.datetime.combine(
            hoy - datetime.timedelta(days=ejemplo.dias_atras),
            datetime.time(9 + indice % 4),
            tzinfo=zona,
        )
        escritas.append(clave)
        if almacen.exists(clave):
            # De una carga anterior que falló sin poder borrarlo.
            almacen.delete(clave)
        if almacen.save(clave, ContentFile(contenido)) != clave:
            raise RuntimeError("El almacenamiento guardó el archivo con otra clave.")
        Sesion.objects.create(
            id=id_sesion,
            institucion=institucion,
            autor=cuenta,
            subido_por=cuenta,
            grado=ejemplo.grado,
            grado_hasta=ejemplo.grado,
            area=areas[ejemplo.area % len(areas)],
            titulo=ejemplo.titulo,
            proposito=ejemplo.proposito,
            origen=Sesion.Origen.PROPIA,
            estado=Sesion.Estado.ENVIADA,
            compartida=ejemplo.compartida,
            terminos_aceptados_en=creado if ejemplo.compartida else None,
            archivo_clave=clave,
            archivo_nombre=f"{ejemplo.titulo.lower()}{_EXTENSION[ejemplo.formato]}",
            tipo_mime=tipo,
            tamano_bytes=len(contenido),
            texto=texto,
            texto_busqueda=servicios.texto_de_busqueda(ejemplo.titulo, ejemplo.proposito, texto),
        )
        # ``auto_now_add`` no se aplica en ``update()``: así la sesión queda en su día.
        Sesion.objects.filter(pk=id_sesion).update(creado_en=creado)
        creadas += 1
    return creadas


def sesiones_demo():
    """Las sesiones cuya autora es una cuenta demo, también las que envió desde la pantalla."""
    return Sesion.objects.filter(autor__es_demo=True)


def quitar_sesiones():
    """Borra las sesiones demo y sus archivos, con la regla de la docente, y las vistas que las
    cuentas demo dejaron en sesiones reales. Va dentro de una transacción; devuelve cuántas
    sesiones borró. No deja SESION_ELIMINADA: el resumen va en DEMO_QUITADA (D11)."""
    borradas = servicios.borrar_sesiones(sesiones_demo())
    SesionVista.objects.filter(usuario__es_demo=True).delete()
    return borradas
