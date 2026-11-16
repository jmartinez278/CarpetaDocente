"""Archivos ficticios para las pruebas de repositorio: PDF, DOCX y los que se disfrazan (D6).

Se arman en memoria con lo mínimo que tiene cada formato real; ninguno trae datos de nadie.
"""

import io
import secrets
import zipfile
from xml.sax.saxutils import escape

from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader, PdfWriter

# Tipo de la parte principal de un .docx y de un .docm ([Content_Types].xml).
PRINCIPAL_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
PRINCIPAL_DOCM = "application/vnd.ms-word.document.macroEnabled.main+xml"

_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    b"2 0 obj << /Type /Pages /Kids [] /Count 0 >> endobj\n"
    b"trailer << /Root 1 0 R >>\n"
    b"%%EOF\n"
)


def _tipos(principal, relleno=0):
    """``[Content_Types].xml`` con la parte principal; ``relleno`` bytes de comentario antes."""
    comentario = f"<!--{'x' * relleno}-->" if relleno else ""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"{comentario}"
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/word/document.xml" ContentType="{principal}"/>'
        "</Types>"
    ).encode()


def zip_de(partes):
    """Un ZIP en memoria con ``partes`` (nombre → bytes)."""
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as paquete:
        for nombre, contenido in partes.items():
            paquete.writestr(nombre, contenido)
    return salida.getvalue()


def pdf_bytes(tamano=None):
    """Un PDF mínimo; con ``tamano``, relleno con un comentario hasta esos bytes exactos."""
    if tamano is None:
        return _PDF
    return _PDF + b"%" + b"x" * (tamano - len(_PDF) - 2) + b"\n"


def docx_bytes(principal=PRINCIPAL_DOCX, documento=True, relleno=0, tipos=None, extras=None):
    """Un .docx mínimo; ``tipos`` reemplaza ``[Content_Types].xml`` y ``extras`` agrega partes."""
    partes = {
        "[Content_Types].xml": _tipos(principal, relleno) if tipos is None else tipos,
        "_rels/.rels": b'<?xml version="1.0"?><Relationships/>',
    }
    if documento:
        partes["word/document.xml"] = (
            b'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
            b'wordprocessingml/2006/main"><w:body><w:p/></w:body></w:document>'
        )
    partes.update(extras or {})
    return zip_de(partes)


_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def documento_xml(cuerpo, antes=""):
    """``word/document.xml`` con ``cuerpo`` (XML de ``w:body``); ``antes`` va tras la cabecera."""
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>{antes}'
        f'<w:document xmlns:w="{_NS_W}"><w:body>{cuerpo}</w:body></w:document>'
    ).encode()


def parrafos_xml(parrafos):
    """Un ``w:p`` con un solo ``w:t`` por cada texto de ``parrafos``."""
    return "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>'
        for texto in parrafos
    )


def docx_con_texto(parrafos):
    """Un .docx válido cuyo cuerpo son ``parrafos``."""
    return docx_bytes(extras={"word/document.xml": documento_xml(parrafos_xml(parrafos))})


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


def pdf_cifrado(paginas):
    """El mismo PDF con contraseña: no se puede leer sin ella."""
    escritor = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf_con_texto(paginas))))
    escritor.encrypt(secrets.token_hex(8), algorithm="RC4-128")
    salida = io.BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def subido(nombre, contenido, tipo="application/octet-stream"):
    """Lo que Django entrega en ``request.FILES``; ``tipo`` es lo que dice el navegador."""
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)


def pdf(nombre="leemos-un-cuento.pdf", tamano=None):
    return subido(nombre, pdf_bytes(tamano), "application/pdf")


def docx(nombre="leemos-un-cuento.docx", **opciones):
    return subido(nombre, docx_bytes(**opciones))
