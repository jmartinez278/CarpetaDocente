"""Texto transcrito de un archivo y regla de búsqueda (spec repositorio-sesiones, «Texto
transcrito»; design de US-011, D2 y D4).

``extraer_texto`` nunca lanza: lo que no se puede leer queda sin texto. No toca la base.
"""

import io
import logging
from importlib import import_module

import pytest

from repositorio import texto
from repositorio.models import TIPO_DOCX, TIPO_PDF
from repositorio.tests.archivos import (
    documento_xml,
    docx_bytes,
    docx_con_texto,
    parrafos_xml,
    pdf_bytes,
    pdf_cifrado,
    pdf_con_texto,
)


def extraer(contenido, tipo):
    return texto.extraer_texto(io.BytesIO(contenido), tipo)


def docx_de(cuerpo, antes=""):
    return docx_bytes(extras={"word/document.xml": documento_xml(cuerpo, antes)})


# --- .docx -----------------------------------------------------------------------------------


def test_un_docx_da_una_linea_por_parrafo():
    # Escenario «Word».
    contenido = docx_con_texto(["Formamos equipos", "Leemos el cuento «La amistad»"])

    assert extraer(contenido, TIPO_DOCX) == "Formamos equipos\nLeemos el cuento «La amistad»"


def test_un_docx_respeta_tabulaciones_saltos_y_texto_partido_en_tramos():
    cuerpo = (
        "<w:p><w:r><w:t>Nombre:</w:t><w:tab/><w:t>Fecha:</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Inicio</w:t><w:br/><w:t>Desarrollo</w:t></w:r></w:p>"
        '<w:p><w:r><w:t xml:space="preserve">Lista de </w:t></w:r>'
        "<w:r><w:t>cotejo</w:t></w:r></w:p>"
    )

    assert extraer(docx_de(cuerpo), TIPO_DOCX) == (
        "Nombre: Fecha:\nInicio\nDesarrollo\nLista de cotejo"
    )


def test_un_docx_no_trae_lo_que_no_es_texto_del_cuerpo():
    cuerpo = (
        "<w:p><w:pPr><w:pStyle w:val='Titulo'/></w:pPr><w:r><w:t>Cierre</w:t>"
        "<w:instrText>PAGE</w:instrText><w:delText>borrado</w:delText></w:r></w:p>"
    )

    assert extraer(docx_de(cuerpo), TIPO_DOCX) == "Cierre"


def test_un_docx_sin_texto_queda_vacio():
    assert extraer(docx_bytes(), TIPO_DOCX) == ""


def test_un_docx_largo_se_recorta_a_100_000_caracteres():
    contenido = docx_con_texto(["palabras " * 1000] * 20)

    extraido = extraer(contenido, TIPO_DOCX)

    assert len(extraido) == texto.MAXIMO_CARACTERES == 100_000
    assert extraido.startswith("palabras palabras")


@pytest.mark.parametrize(
    "contenido",
    [
        b"PK\x03\x04 esto no es un ZIP entero",
        b"",
        docx_bytes(documento=False),
        docx_de("<w:p><w:r><w:t>sin cerrar"),
        docx_de(
            "<w:p><w:r><w:t>&a;</w:t></w:r></w:p>", antes='<!DOCTYPE d [<!ENTITY a "Formamos">]>'
        ),
    ],
    ids=["zip-roto", "vacio", "sin-documento", "xml-roto", "doctype"],
)
def test_un_docx_que_no_se_puede_leer_queda_sin_texto(contenido):
    # Escenario «Archivo que no se puede leer».
    assert extraer(contenido, TIPO_DOCX) == ""


def test_un_documento_que_declara_mas_de_8_mb_no_se_lee():
    # El texto va antes del relleno: si se leyera hasta el tope, saldría.
    relleno = b"<!--" + b"x" * texto.MAXIMO_DOCUMENTO + b"-->"
    documento = documento_xml(parrafos_xml(["Formamos equipos"])) + relleno
    justo = documento_xml(parrafos_xml(["Formamos equipos"]))
    justo += b"<!--" + b"x" * (texto.MAXIMO_DOCUMENTO - len(justo) - 7) + b"-->"
    assert len(justo) == texto.MAXIMO_DOCUMENTO == 8 * 1024 * 1024

    assert extraer(docx_bytes(extras={"word/document.xml": documento}), TIPO_DOCX) == ""
    assert extraer(docx_bytes(extras={"word/document.xml": justo}), TIPO_DOCX) == (
        "Formamos equipos"
    )


# --- PDF -------------------------------------------------------------------------------------


def test_un_pdf_con_capa_de_texto_da_su_texto():
    # Escenario «PDF con texto».
    contenido = pdf_con_texto([["Formamos equipos", "El niño escribe una recomendación"], ["Fin"]])

    assert extraer(contenido, TIPO_PDF) == (
        "Formamos equipos\nEl niño escribe una recomendación\nFin"
    )


@pytest.mark.parametrize(
    "contenido",
    [pdf_con_texto([[], []]), pdf_bytes(), pdf_cifrado([["Formamos equipos"]]), b"%PDF-1.4\nroto"],
    ids=["sin-texto", "sin-paginas", "cifrado", "roto"],
)
def test_un_pdf_sin_texto_cifrado_o_roto_queda_sin_texto(contenido):
    # Escenarios «PDF escaneado» y «Archivo que no se puede leer».
    assert extraer(contenido, TIPO_PDF) == ""


def test_de_un_pdf_de_60_paginas_solo_se_leen_las_40_primeras():
    contenido = pdf_con_texto([[f"pagina{numero:02d}"] for numero in range(1, 61)])

    lineas = extraer(contenido, TIPO_PDF).split("\n")

    assert lineas == [f"pagina{numero:02d}" for numero in range(1, 41)]


def test_un_pdf_deja_de_leerse_al_llegar_a_100_000_caracteres(monkeypatch):
    contenido = pdf_con_texto([["palabra " * 9] * 50 for _ in range(40)])
    leidas = []
    pagina = import_module("pypdf").PageObject
    original = pagina.extract_text

    def contar(self, *args, **kwargs):
        leidas.append(1)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(pagina, "extract_text", contar)

    extraido = extraer(contenido, TIPO_PDF)

    assert 99_000 < len(extraido) <= 100_000
    assert len(leidas) < 40


# --- Lo común --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("contenido", "tipo"),
    [
        (docx_con_texto(["Formamos equipos"]), TIPO_DOCX),
        (pdf_con_texto([["Formamos equipos"]]), TIPO_PDF),
        (b"PK\x03\x04 roto", TIPO_DOCX),
        (b"%PDF-1.4\nroto", TIPO_PDF),
        (b"hola", "text/plain"),
    ],
    ids=["docx", "pdf", "docx-roto", "pdf-roto", "otro-tipo"],
)
def test_el_archivo_queda_al_principio(contenido, tipo):
    archivo = io.BytesIO(contenido)
    archivo.seek(3)

    texto.extraer_texto(archivo, tipo)

    assert archivo.tell() == 0


def test_un_tipo_que_no_es_pdf_ni_docx_queda_sin_texto():
    assert extraer(b"Formamos equipos", "text/plain") == ""


def test_un_archivo_que_no_se_deja_leer_queda_sin_texto_y_avisa_sin_su_nombre(caplog):
    class Roto(io.BytesIO):
        name = "Sesion de Ana Quispe.pdf"

        def read(self, *args):
            raise OSError("se cortó la lectura de Sesion de Ana Quispe.pdf")

        def seek(self, *args):
            raise OSError("se cortó la lectura de Sesion de Ana Quispe.pdf")

    with caplog.at_level(logging.WARNING, logger="repositorio.texto"):
        assert texto.extraer_texto(Roto(b"%PDF-1.4"), TIPO_PDF) == ""

    avisos = [registro.getMessage() for registro in caplog.records]
    assert any("OSError" in aviso for aviso in avisos)
    assert not any("Quispe" in aviso for aviso in avisos)
    assert all(registro.exc_info is None for registro in caplog.records)


def test_un_archivo_sin_texto_no_avisa(caplog):
    with caplog.at_level(logging.WARNING, logger="repositorio.texto"):
        extraer(pdf_con_texto([[]]), TIPO_PDF)

    assert not caplog.records


# --- Limpieza --------------------------------------------------------------------------------


def test_limpiar_quita_el_nul_y_los_caracteres_de_control():
    # PostgreSQL rechaza el NUL en un texto.
    assert texto.limpiar("Forma\x00mos\x07 equi\x1bpos﻿​") == "Formamos equipos"


def test_limpiar_quita_medios_pares_sustitutos():
    assert texto.limpiar("Inicio \ud83d cierre") == "Inicio cierre"


def test_limpiar_reduce_espacios_y_deja_a_lo_mas_dos_saltos():
    sucio = "  Inicio \t  de   la sesión  \r\n\n\n\n\n  Cierre\r\rFin\f\v.  \n\n"

    assert texto.limpiar(sucio) == "Inicio de la sesión\n\nCierre\n\nFin ."


def test_limpiar_recorta_a_100_000_caracteres():
    assert len(texto.limpiar("a" * 100_001)) == 100_000


# --- Regla de búsqueda (D4) ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Recomendación", "recomendacion"),
        ("ÁRBOL", "arbol"),
        ("niño", "nino"),
        ("  Lista   de\n\tcotejo ", "lista de cotejo"),
        ("Straße ﬁn", "strasse fin"),
        ("", ""),
    ],
)
def test_normalizar_quita_tildes_mayusculas_y_espacios_de_mas(entrada, esperado):
    assert texto.normalizar(entrada) == esperado


def test_normalizar_da_lo_mismo_que_la_migracion_0002():
    # La migración llenó ``texto_busqueda`` de las sesiones anteriores con su copia de la regla.
    migracion = import_module("repositorio.migrations.0002_texto_vistas_y_terminos")
    textos = [
        "Escribimos recomendaciones para cuidar el agua Que escriban una recomendación.",
        "ÁRBOL  genealógico\nde   mi FAMILIA ",
        "El niño y la niña cuentan hasta 10 ½",
    ]

    for original in textos:
        assert texto.normalizar(original) == migracion._normalizar(original)
