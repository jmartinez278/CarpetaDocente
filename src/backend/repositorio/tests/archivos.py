"""Archivos ficticios para las pruebas de repositorio: PDF, DOCX y los que se disfrazan (D6).

Se arman en memoria con lo mínimo que tiene cada formato real; ninguno trae datos de nadie.
"""

import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile

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


def docx_bytes(principal=PRINCIPAL_DOCX, documento=True, relleno=0):
    partes = {
        "[Content_Types].xml": _tipos(principal, relleno),
        "_rels/.rels": b'<?xml version="1.0"?><Relationships/>',
    }
    if documento:
        partes["word/document.xml"] = (
            b'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
            b'wordprocessingml/2006/main"><w:body><w:p/></w:body></w:document>'
        )
    return zip_de(partes)


def subido(nombre, contenido, tipo="application/octet-stream"):
    """Lo que Django entrega en ``request.FILES``; ``tipo`` es lo que dice el navegador."""
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)


def pdf(nombre="leemos-un-cuento.pdf", tamano=None):
    return subido(nombre, pdf_bytes(tamano), "application/pdf")


def docx(nombre="leemos-un-cuento.docx", **opciones):
    return subido(nombre, docx_bytes(**opciones))
