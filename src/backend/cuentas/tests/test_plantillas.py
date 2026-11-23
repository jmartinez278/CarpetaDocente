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
        # Selector de la semana y leyenda de la asistencia (US-030, D10).
        "chevron-left",
        "chevron-right",
        # ☰ del marco del rebrand y su destino Inicio (rebrand-base, D4 y D6).
        "menu",
        "house",
        # «Tu selección» y «Deshacer cambios» de Competencias (rebrand-us-029, D4).
        "list-checks",
        "undo-2",
        # Pestañas, buscador, filtros y página de la sesión (US-011, tarea 5.2).
        "download",
        "external-link",
        "plus",
        "search",
        "sliders-horizontal",
        "trash-2",
        # Botón de tema (T-04, US-040): la luna en claro y el sol en oscuro.
        "sun",
        "moon",
    }
    assert "ISC License" in (CARPETA_ICONOS / "LICENSE-lucide.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize("icono", ICONOS, ids=lambda p: p.name)
def test_icono_con_trazo_hereda_color_y_oculto_al_lector(icono):
    svg = icono.read_text(encoding="utf-8")

    assert 'stroke="currentColor"' in svg
    assert 'stroke-width="1.6"' in svg
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


# Botón de tema (T-04; spec pantallas-de-inicio «Temas claro y oscuro»; US-040, D1).
def _html(respuesta):
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def _etiqueta_del_script_de_tema(html):
    cabeza = re.search(r"<head\b.*?</head>", html, re.DOTALL)
    assert cabeza, "la página no tiene <head>"
    scripts = re.findall(r"<script\b[^>]*js/tema\.js[^>]*>", cabeza.group(0))
    assert len(scripts) == 1, "tema.js debe cargarse una sola vez, dentro de <head>"
    return cabeza.group(0), scripts[0]


def test_base_carga_tema_js_en_el_head_antes_de_la_hoja_y_sin_defer():
    from django.template.loader import render_to_string

    cabeza, etiqueta = _etiqueta_del_script_de_tema(render_to_string("base.html"))

    assert cabeza.index(etiqueta) < cabeza.index("dist/app.css")
    assert "defer" not in etiqueta
    assert "async" not in etiqueta
    assert 'type="module"' not in etiqueta


def test_marco_pinta_el_boton_de_tema_antes_del_menu_de_la_cuenta(client, docente):
    client.force_login(docente)

    html = _html(client.get("/docente/sin-permiso/"))

    botones = re.findall(r"<button\b[^>]*\bdata-tema\b[^>]*>", html)
    assert len(botones) == 1
    assert 'aria-label="Cambiar a tema oscuro"' in botones[0]
    assert 'type="button"' in botones[0]
    barra = re.search(r"<header\b.*?</header>", html, re.DOTALL).group(0)
    assert barra.index("data-tema") < barra.index("data-menu-cuenta")


def test_el_boton_de_tema_lleva_sol_y_luna_decorativos(client, docente):
    client.force_login(docente)

    html = _html(client.get("/docente/sin-permiso/"))

    boton = re.search(r"<button\b[^>]*\bdata-tema\b.*?</button>", html, re.DOTALL).group(0)
    assert boton.count("<svg") == 2
    assert boton.count('aria-hidden="true"') == 2
    assert "data-icono-luna" in boton
    assert "data-icono-sol" in boton


def test_el_ingreso_lleva_el_boton_de_tema(client):
    html = _html(client.get("/ingresar/"))

    _etiqueta_del_script_de_tema(html)
    botones = re.findall(r"<button\b[^>]*\bdata-tema\b[^>]*>", html)
    assert len(botones) == 1
    assert 'aria-label="Cambiar a tema oscuro"' in botones[0]


def test_el_panel_de_administracion_no_lleva_boton_de_tema(client, administrador):
    client.force_login(administrador)

    html = _html(client.get("/admin/"))

    assert "data-tema" not in html
    assert "js/tema.js" not in html
