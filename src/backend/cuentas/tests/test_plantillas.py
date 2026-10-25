"""Las plantillas no llevan colores escritos ni estilos en línea (US-001, D5)."""

import re
from pathlib import Path

import pytest

RAIZ_BACKEND = Path(__file__).resolve().parents[2]
COLOR_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
ESTILO_EN_LINEA = re.compile(r"style=")

PLANTILLAS = sorted(RAIZ_BACKEND.glob("**/templates/**/*.html"))


def hallazgos(texto):
    return COLOR_HEX.findall(texto) + ESTILO_EN_LINEA.findall(texto)


def test_se_encuentran_las_plantillas():
    assert PLANTILLAS, "la búsqueda no halló ninguna plantilla: la ruta está mal"


@pytest.mark.parametrize(
    "plantilla", PLANTILLAS, ids=lambda p: p.relative_to(RAIZ_BACKEND).as_posix()
)
def test_plantilla_sin_colores_ni_estilos_en_linea(plantilla):
    assert hallazgos(plantilla.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "texto", ['<p class="x" style="color: red">', '<p class="text-[#5b2610]">', "<i>#fff</i>"]
)
def test_el_detector_reconoce_un_color_o_un_estilo(texto):
    assert hallazgos(texto)


# Íconos de Lucide incrustados con {% include "iconos/<nombre>.svg" %} (D9, R-20).
CARPETA_ICONOS = RAIZ_BACKEND / "templates" / "iconos"
ICONOS = sorted(CARPETA_ICONOS.glob("*.svg"))
INCLUDE_DE_ICONO = re.compile(r"""\{%\s*include\s+["'](iconos/[^"']+)["']""")


def test_los_iconos_de_d9_estan_y_llevan_el_aviso_isc():
    nombres = {icono.stem for icono in ICONOS}

    assert nombres == {
        "eye",
        "eye-off",
        "circle-alert",
        "arrow-right",
        "book-open",
        "clipboard-list",
        "calendar-check",
        "inbox",
        # Miniaturas de la portada (DESIGN.md, Iconografía): archivos Word y PDF, Asistió y Faltó.
        "file-text",
        "check",
        "x",
        # Menú de la cuenta y aviso de inactividad (US-002, design.md D4 y D5).
        "circle-user-round",
        "log-out",
        "clock",
    }
    assert "ISC License" in (CARPETA_ICONOS / "LICENSE-lucide.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize("icono", ICONOS, ids=lambda p: p.name)
def test_icono_con_trazo_hereda_color_y_oculto_al_lector(icono):
    svg = icono.read_text(encoding="utf-8")

    assert 'stroke="currentColor"' in svg
    assert 'stroke-width="1.75"' in svg
    assert 'aria-hidden="true"' in svg
    assert 'focusable="false"' in svg


def test_cada_include_de_icono_resuelve_un_archivo():
    includes = {
        ruta
        for plantilla in PLANTILLAS
        for ruta in INCLUDE_DE_ICONO.findall(plantilla.read_text(encoding="utf-8"))
    }

    faltan = {ruta for ruta in includes if not (RAIZ_BACKEND / "templates" / ruta).is_file()}
    assert faltan == set()
