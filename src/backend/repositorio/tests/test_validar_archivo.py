"""Validación del archivo de una sesión (spec envio-sesiones, «Archivo PDF o Word de hasta 4 MB»;
spec almacenamiento-archivos, «Clave del archivo»; design D6).

El tipo sale del contenido y debe coincidir con la extensión; el del navegador no cuenta.
"""

import zipfile

import pytest
from django.core.exceptions import ValidationError

from repositorio import servicios
from repositorio.models import TAMANO_MAXIMO, TIPO_DOCX, TIPO_PDF
from repositorio.tests.archivos import (
    PRINCIPAL_DOCM,
    PRINCIPAL_DOCX,
    docx,
    docx_bytes,
    pdf,
    pdf_bytes,
    subido,
    zip_de,
)

NO_ES = "Este archivo no es PDF ni Word (.docx). Elige otro archivo."
MUY_GRANDE = "El archivo supera los 4 MB. Elige uno más pequeño."
FALTA = "Elige un archivo PDF o Word (.docx)."


def rechazo(archivo):
    with pytest.raises(ValidationError) as error:
        servicios.validar_archivo(archivo)
    return error.value.messages


def test_un_pdf_real_pasa_con_su_tipo_y_su_tamano():
    archivo = pdf()

    valido = servicios.validar_archivo(archivo)

    assert valido.tipo_mime == TIPO_PDF
    assert valido.extension == ".pdf"
    assert valido.nombre == "leemos-un-cuento.pdf"
    assert valido.tamano == len(pdf_bytes())


def test_un_docx_real_pasa_con_su_tipo():
    valido = servicios.validar_archivo(docx())

    assert valido.tipo_mime == TIPO_DOCX
    assert valido.extension == ".docx"


def test_la_extension_en_mayusculas_tambien_pasa():
    assert servicios.validar_archivo(pdf("SESION.PDF")).extension == ".pdf"


def test_el_tipo_que_dice_el_navegador_no_cuenta():
    archivo = subido("sesion.pdf", pdf_bytes(), "image/jpeg")

    assert servicios.validar_archivo(archivo).tipo_mime == TIPO_PDF


def test_despues_de_validar_el_archivo_queda_al_principio():
    archivo = docx()

    servicios.validar_archivo(archivo)

    assert archivo.read(2) == b"PK"


def test_justo_4_mb_pasa():
    # Escenario «Justo 4 MB».
    archivo = pdf(tamano=TAMANO_MAXIMO)
    assert archivo.size == 4_194_304

    assert servicios.validar_archivo(archivo).tamano == TAMANO_MAXIMO


def test_un_byte_mas_de_4_mb_se_rechaza():
    # Escenario «Archivo de más de 4 MB».
    assert rechazo(pdf(tamano=TAMANO_MAXIMO + 1)) == [MUY_GRANDE]


def test_sin_archivo_lo_pide():
    # Escenario «Sin archivo».
    assert rechazo(None) == [FALTA]


@pytest.mark.parametrize(
    "archivo",
    [
        subido("sesion.pdf", b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 120),
        subido("sesion.pdf", docx_bytes()),
        subido("sesion.docx", zip_de({"[Content_Types].xml": b"<Types/>", "hola.txt": b"hola"})),
        subido("sesion.docx", docx_bytes(documento=False)),
        subido("sesion.docx", docx_bytes(principal=PRINCIPAL_DOCM)),
        subido("sesion.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 504),
        subido("sesion.docx", pdf_bytes()),
        subido("sesion.pdf", b""),
        subido("sesion.pdf", b"%PDF"),
        subido("sesion.docx", b"PK\x03\x04 esto no es un zip"),
        subido("sesion", pdf_bytes()),
        subido("sesion.jpg", pdf_bytes()),
    ],
    ids=[
        "exe-llamado-pdf",
        "docx-llamado-pdf",
        "zip-sin-word-document",
        "docx-sin-word-document",
        "docm-renombrado",
        "doc",
        "pdf-llamado-docx",
        "vacio",
        "cabecera-incompleta",
        "zip-roto",
        "sin-extension",
        "pdf-llamado-jpg",
    ],
)
def test_un_archivo_que_no_es_pdf_ni_docx_se_rechaza(archivo):
    # Escenarios «Tipo no permitido» y «Envío que salta el navegador».
    assert rechazo(archivo) == [NO_ES]


def test_content_types_de_mas_de_64_kb_no_se_lee_entero(monkeypatch):
    # La declaración queda después de los primeros 64 KB: no se ve, y se rechaza.
    archivo = subido("sesion.docx", docx_bytes(relleno=70_000))
    pedidos = []
    leer = zipfile.ZipExtFile.read

    def espiar(self, n=-1):
        pedidos.append(n)
        return leer(self, n)

    monkeypatch.setattr(zipfile.ZipExtFile, "read", espiar)

    assert rechazo(archivo) == [NO_ES]
    assert pedidos
    assert all(0 < n <= 64 * 1024 for n in pedidos)


# --- [Content_Types].xml se lee como XML, no como bytes (A2, hallazgo 3) ---------------------

_NS = 'xmlns="http://schemas.openxmlformats.org/package/2006/content-types"'
_CABECERA = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def _tipos_xml(cuerpo, antes=""):
    return f"{_CABECERA}{antes}<Types {_NS}>{cuerpo}</Types>".encode()


def _override(parte, tipo):
    return f'<Override PartName="{parte}" ContentType="{tipo}"/>'


@pytest.mark.parametrize(
    "contenido",
    [
        docx_bytes(
            tipos=_tipos_xml(
                f"<!-- {PRINCIPAL_DOCX} -->" + _override("/word/document.xml", PRINCIPAL_DOCM)
            )
        ),
        docx_bytes(
            tipos=_tipos_xml(
                _override("/word/document.xml", PRINCIPAL_DOCM),
                antes=f"<!-- {PRINCIPAL_DOCX} -->",
            ),
            extras={"word/vbaProject.bin": b"\x00macro"},
        ),
        docx_bytes(
            tipos=_tipos_xml(
                _override("/word/document.xml", PRINCIPAL_DOCM)
                + f'<Default Extension="docx" ContentType="{PRINCIPAL_DOCX}"/>'
            )
        ),
    ],
    ids=["comentario-dentro", "comentario-antes-y-vba", "tipo-docx-en-otro-lugar"],
)
def test_un_docm_con_el_tipo_docx_escondido_se_rechaza(contenido):
    # Prueba adversarial: la cadena del .docx aparece, pero la parte principal es de un .docm.
    assert rechazo(subido("sesion.docx", contenido)) == [NO_ES]


def test_un_docx_con_vba_project_se_rechaza():
    contenido = docx_bytes(extras={"word/vbaProject.bin": b"\x00macro"})

    assert rechazo(subido("sesion.docx", contenido)) == [NO_ES]


def test_macro_enabled_en_cualquier_parte_se_rechaza():
    tipos = _tipos_xml(
        _override("/word/document.xml", PRINCIPAL_DOCX)
        + _override("/word/vbaData.xml", "application/vnd.ms-word.vbaData+xml")
        + _override("/word/x.xml", "application/vnd.ms-office.macroEnabled+xml")
    )

    assert rechazo(subido("sesion.docx", docx_bytes(tipos=tipos))) == [NO_ES]


@pytest.mark.parametrize(
    "tipos",
    [
        _tipos_xml(""),
        _tipos_xml(
            _override("/word/document.xml", PRINCIPAL_DOCX)
            + _override("/word/document.xml", PRINCIPAL_DOCM)
        ),
        _tipos_xml(_override("/word/document.xml", PRINCIPAL_DOCX + " ")),
        f'{_CABECERA}<Types><Override PartName="/word/document.xml" '
        f'ContentType="{PRINCIPAL_DOCX}"/></Types>'.encode(),
        f'{_CABECERA}<!DOCTYPE Types [<!ENTITY t "{PRINCIPAL_DOCX}">]>'
        f'<Types {_NS}><Override PartName="/word/document.xml" ContentType="&t;"/>'
        "</Types>".encode(),
        b"<Types",
    ],
    ids=["sin-override", "dos-override", "tipo-casi-igual", "sin-namespace", "doctype", "xml-roto"],
)
def test_content_types_sin_un_override_docx_exacto_se_rechaza(tipos):
    assert rechazo(subido("sesion.docx", docx_bytes(tipos=tipos))) == [NO_ES]


def test_un_docx_como_los_de_word_pasa():
    # Word declara también estilos, ajustes y propiedades; la parte principal con mayúsculas
    # distintas sigue siendo la misma (los nombres de parte no distinguen mayúsculas).
    tipos = _tipos_xml(
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + _override("/Word/Document.xml", PRINCIPAL_DOCX)
        + _override(
            "/word/styles.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
        )
        + _override(
            "/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"
        )
    )

    assert servicios.validar_archivo(docx(tipos=tipos)).tipo_mime == TIPO_DOCX


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("leemos-un-cuento.pdf", "leemos-un-cuento.pdf"),
        ("C:\\Users\\ana\\Documentos\\sesion.pdf", "sesion.pdf"),
        ("../../etc/sesion.pdf", "sesion.pdf"),
        ("  Leemos un cuento.pdf  ", "Leemos un cuento.pdf"),
    ],
)
def test_nombre_limpio_sin_rutas(nombre, esperado):
    # Escenario «Nombre original largo o con rutas».
    assert servicios.nombre_limpio(nombre) == esperado


def test_nombre_de_300_caracteres_se_recorta_a_255_con_su_extension():
    nombre = "a" * 296 + ".pdf"

    limpio = servicios.nombre_limpio(nombre)

    assert len(limpio) == 255
    assert limpio == "a" * 251 + ".pdf"


def test_el_archivo_validado_trae_el_nombre_limpio():
    archivo = pdf("x" * 296 + ".pdf")

    assert servicios.validar_archivo(archivo).nombre == "x" * 251 + ".pdf"
