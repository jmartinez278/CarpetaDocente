"""Texto transcrito del archivo de una sesión y regla de búsqueda (design de US-011, D2 y D4).

``extraer_texto`` lee lo que una docente autenticada subió: un archivo puede venir dañado,
cifrado o armado para gastar memoria. Por eso tiene topes (páginas, tamaño al descomprimir y
caracteres) y nunca lanza: lo que no se puede leer queda sin texto y la sesión se envía igual.

El texto puede traer lo que la docente escribió (RN-015): de aquí no sale al log ni el texto ni
el nombre del archivo.
"""

import contextlib
import logging
import re
import time
import unicodedata
import zipfile
from xml.etree import ElementTree

from pypdf import Configuration, PdfReader, apply_configuration

from repositorio.models import TAMANO_MAXIMO, TIPO_DOCX, TIPO_PDF

logger = logging.getLogger(__name__)

# Con ``strict=False`` pypdf se recupera de un PDF dañado y avisa citando cadenas del documento
# (por ejemplo, una clave de diccionario repetida): lo que la docente escribió llegaría al log
# (RN-015). Ningún aviso de pypdf sale; el error que importa ya lo cuenta ``extraer_texto``.
logging.getLogger("pypdf").setLevel(logging.CRITICAL + 1)

# Lo que se guarda de una sesión (decisión 8).
MAXIMO_CARACTERES = 100_000
MAXIMO_PAGINAS = 40
# Tope de ``word/document.xml`` ya descomprimido: un .docx de 4 MB real queda muy por debajo.
MAXIMO_DOCUMENTO = 8 * 1024 * 1024
_TROZO = 64 * 1024
# Topes de pypdf mientras se lee un PDF. Los de fábrica dejan 75 MB por flujo (y 300 MB de trabajo
# de decodificación): un archivo de 4 MB puede pedir mucha memoria y CPU antes de que corran los
# topes de páginas y de caracteres. Aquí el flujo de una página cabe en lo mismo que un .docx.
_TOPES_PDF = Configuration().with_overwrites(
    maximum_declared_stream_length=TAMANO_MAXIMO,
    array_based_stream_maximum_output_length=MAXIMO_DOCUMENTO,
    zlib_maximum_output_length=MAXIMO_DOCUMENTO,
    lzw_maximum_output_length=MAXIMO_DOCUMENTO,
    run_length_maximum_output_length=MAXIMO_DOCUMENTO,
    jbig2_maximum_output_length=MAXIMO_DOCUMENTO,
    image_maximum_buffer_size=MAXIMO_DOCUMENTO,
    stream_decoding_work_maximum_length=2 * MAXIMO_DOCUMENTO,
    stream_parsing_work_maximum_count=500_000,
    xform_maximum_invocations_per_extraction=200,
    array_maximum_element_count=20_000,
    dictionary_maximum_element_count=20_000,
    jbig2dec_binary=None,
)
# Tiempo total para leer un PDF; al pasarse se queda con lo leído hasta entonces.
MAXIMO_SEGUNDOS = 5.0

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_TEXTO, _PARRAFO, _TABULACION = f"{_W}t", f"{_W}p", f"{_W}tab"
_SALTOS = {f"{_W}br", f"{_W}cr"}

_FIN_DE_LINEA = re.compile(r"\r\n?")
# Todo espacio que no sea salto de línea: tabulación, espacio duro, salto de página…
_ESPACIOS = re.compile(r"[^\S\n]+")
# Caracteres de control, de formato (ancho cero, guion opcional, marcas de dirección), de uso
# privado y medios pares sustitutos. PostgreSQL rechaza el NUL y un sustituto suelto.
_CONTROL = re.compile(
    "[\x00-\x09\x0b-\x1f\x7f-\x9f\u00ad\u061c\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff\ufff9-\ufffb\ud800-\udfff\ue000-\uf8ff]"
)
_VARIOS_ESPACIOS = re.compile(r" {2,}")
_BORDE_DE_LINEA = re.compile(r" ?\n ?")
_VARIOS_SALTOS = re.compile(r"\n{3,}")


def normalizar(texto):
    """``texto`` como lo recorre la búsqueda: sin tildes, sin mayúsculas y con un solo espacio.

    «Recomendación» → «recomendacion»; «niño» → «nino». Es la misma regla que la copia fija de
    la migración ``repositorio/0002``.
    """
    sin_marcas = "".join(
        letra for letra in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(letra)
    )
    return " ".join(sin_marcas.casefold().split())


def limpiar(texto):
    """``texto`` listo para guardar: sin caracteres de control, con un solo espacio entre
    palabras, no más de una línea en blanco seguida y recortado a 100 000 caracteres."""
    texto = _FIN_DE_LINEA.sub("\n", texto)
    texto = _ESPACIOS.sub(" ", texto)
    texto = _CONTROL.sub("", texto)
    texto = _VARIOS_ESPACIOS.sub(" ", texto)
    texto = _BORDE_DE_LINEA.sub("\n", texto)
    texto = _VARIOS_SALTOS.sub("\n\n", texto)
    return texto.strip()[:MAXIMO_CARACTERES].rstrip()


class _Cuerpo:
    """Recoge el texto de ``word/document.xml`` mientras se lee, sin armar el árbol.

    Un párrafo (``w:p``) es una línea; ``w:tab`` y ``w:br`` se respetan. Solo cuenta el texto
    de ``w:t``: ni instrucciones de campo ni texto borrado. Con ``<!DOCTYPE>`` corta la lectura,
    como ``_SinDoctype`` de ``servicios``: sin DOCTYPE no hay entidades que expandir.
    """

    def __init__(self):
        self.partes = []
        self.largo = 0
        self._en_texto = False

    def _agregar(self, parte):
        self.partes.append(parte)
        self.largo += len(parte)

    def doctype(self, name, pubid, system):
        raise ValueError("document.xml con DOCTYPE")

    def start(self, tag, attrib):
        if tag == _TEXTO:
            self._en_texto = True
        elif tag == _TABULACION:
            self._agregar("\t")
        elif tag in _SALTOS:
            self._agregar("\n")

    def end(self, tag):
        if tag == _TEXTO:
            self._en_texto = False
        elif tag == _PARRAFO:
            self._agregar("\n")

    def data(self, data):
        if self._en_texto:
            self._agregar(data)

    def close(self):
        return None


def _texto_docx(archivo):
    with zipfile.ZipFile(archivo) as paquete:
        info = next(
            (
                parte
                for parte in paquete.infolist()
                if parte.filename.lower() == "word/document.xml"
            ),
            None,
        )
        # ``zipfile`` no entrega más bytes que los declarados: con este tope basta.
        if info is None or info.file_size > MAXIMO_DOCUMENTO:
            return ""
        cuerpo = _Cuerpo()
        lector = ElementTree.XMLParser(target=cuerpo)  # noqa: S314 - sin DOCTYPE, hasta 8 MB
        with paquete.open(info) as documento:
            leido = 0
            while leido < MAXIMO_DOCUMENTO and cuerpo.largo < MAXIMO_CARACTERES:
                trozo = documento.read(min(_TROZO, MAXIMO_DOCUMENTO - leido))
                if not trozo:
                    # Llegó al final: un XML a medias es un archivo dañado y lanza aquí.
                    lector.close()
                    break
                leido += len(trozo)
                lector.feed(trozo)
    return "".join(cuerpo.partes)


def _texto_pdf(archivo):
    limite = time.monotonic() + MAXIMO_SEGUNDOS
    with apply_configuration(_TOPES_PDF):
        lector = PdfReader(archivo, strict=False)
        if lector.is_encrypted:
            return ""
        paginas, largo = [], 0
        for numero, pagina in enumerate(lector.pages):
            if numero >= MAXIMO_PAGINAS or largo >= MAXIMO_CARACTERES:
                break
            if time.monotonic() > limite:
                logger.warning(
                    "La lectura de un PDF pasó de %s s: se guarda lo leído", MAXIMO_SEGUNDOS
                )
                break
            parte = (pagina.extract_text() or "").strip()
            if parte:
                paginas.append(parte)
                largo += len(parte) + 1
    return "\n".join(paginas)


# Tipo → (cómo se lee, cómo se nombra en el log).
_LECTORES = {TIPO_PDF: (_texto_pdf, "PDF"), TIPO_DOCX: (_texto_docx, "Word")}


def extraer_texto(archivo, tipo_mime):
    """El texto de ``archivo`` (un PDF con capa de texto o un .docx), limpio y recortado.

    Nunca lanza: si el archivo no tiene texto, está cifrado, dañado o pasa de los topes,
    devuelve ``""``. Deja el archivo al principio para guardarlo después.
    """
    leer, nombre = _LECTORES.get(tipo_mime, (None, None))
    try:
        if leer is None:
            return ""
        archivo.seek(0)
        return limpiar(leer(archivo))
    except Exception as error:
        # Solo el tipo del error: su mensaje puede traer contenido o el nombre del archivo.
        logger.warning(
            "No se pudo extraer el texto de un archivo %s: %s", nombre, type(error).__name__
        )
        return ""
    finally:
        with contextlib.suppress(Exception):
            archivo.seek(0)
