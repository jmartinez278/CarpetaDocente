"""Diálogo de la lista de estudiantes en el navegador (spec estudiantes-seccion; US-006, D6 y D10).

Abrir con "Ver estudiantes", cerrar con Esc y "Cerrar" (el foco vuelve al enlace), Atrás que cierra
el diálogo, axe de la portada y de la lista vacía en ambos temas a 360 y 1280 px, y 320 px sin
desplazamiento horizontal.
Necesita el CSS compilado y Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import ANCHOS, TEMAS, con_pantalla, ingresar, revisar_con_axe

pytestmark = pytest.mark.e2e

TITULO = "Estudiantes de 2.º A"


@pytest.fixture
def docente_con_seccion(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return docente


@pytest.fixture
def portada(live_server, page, docente_con_seccion, clave):
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    return page


def ver_estudiantes(page):
    return page.get_by_role("link", name="Ver estudiantes")


def dialogo(page):
    return page.get_by_role("dialog", name=TITULO)


def abrir(page):
    ver_estudiantes(page).click()
    expect(dialogo(page)).to_be_visible()


def test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion(live_server, portada):
    abrir(portada)

    expect(portada.get_by_role("heading", name=TITULO)).to_be_visible()
    expect(dialogo(portada)).to_contain_text("0 estudiantes")
    expect(dialogo(portada)).to_contain_text("Tu sección aún no tiene estudiantes.")
    expect(dialogo(portada).get_by_role("link", name="Agregar uno por uno")).to_be_visible()
    expect(dialogo(portada).get_by_role("link", name="Pegar lista")).to_be_visible()
    expect(portada).to_have_url(f"{live_server.url}/docente/")


def test_el_foco_entra_al_titulo_del_dialogo(portada):
    abrir(portada)

    expect(portada.locator("#modal-titulo")).to_be_focused()


def test_esc_cierra_el_dialogo_y_el_foco_vuelve_al_enlace(portada):
    abrir(portada)

    portada.keyboard.press("Escape")

    expect(dialogo(portada)).to_be_hidden()
    expect(ver_estudiantes(portada)).to_be_focused()


def test_cerrar_cierra_el_dialogo_y_el_foco_vuelve_al_enlace(portada):
    abrir(portada)

    dialogo(portada).get_by_role("button", name="Cerrar").click()

    expect(dialogo(portada)).to_be_hidden()
    expect(ver_estudiantes(portada)).to_be_focused()


def test_atras_cierra_el_dialogo_y_la_portada_sigue(live_server, portada):
    abrir(portada)

    portada.go_back()

    expect(dialogo(portada)).to_be_hidden()
    expect(portada).to_have_url(f"{live_server.url}/docente/")
    expect(portada.get_by_role("heading", name="Hola, Ana Quispe")).to_be_visible()


def test_cerrar_consume_la_entrada_del_historial_y_se_puede_volver_a_abrir(portada):
    assert portada.evaluate("history.state") is None
    abrir(portada)
    assert portada.evaluate("history.state") == {"estudiantes": True}

    portada.keyboard.press("Escape")
    expect(dialogo(portada)).to_be_hidden()
    portada.wait_for_function("history.state === null")

    abrir(portada)
    portada.get_by_role("button", name="Cerrar").click()
    expect(dialogo(portada)).to_be_hidden()
    portada.wait_for_function("history.state === null")


def test_el_dialogo_deja_la_portada_inerte_y_sin_desplazamiento(portada):
    abrir(portada)

    assert portada.evaluate("document.body.classList.contains('con-dialogo')")
    assert portada.evaluate("getComputedStyle(document.body).overflow") == "hidden"
    portada.keyboard.press("Escape")
    expect(portada.locator("body")).not_to_have_class(re.compile("con-dialogo"))


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_portada_con_el_aviso_pasa_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page.locator("#aviso-portada")).to_contain_text("Tu sección aún no tiene estudiantes")

    revisar_con_axe(page, f"portada-aviso-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_vacia_en_el_dialogo_pasa_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir(page)

    revisar_con_axe(page, f"lista-vacia-dialogo-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_vacia_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/")
    expect(page.get_by_role("heading", level=1, name=TITULO)).to_be_visible()

    revisar_con_axe(page, f"lista-vacia-pagina-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", [320, 360, 1280])
def test_la_portada_y_la_lista_vacia_no_se_desplazan_en_horizontal(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho

    abrir(page)
    ancho_del_dialogo = page.evaluate("document.getElementById('estudiantes').scrollWidth")
    assert ancho_del_dialogo <= ancho

    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/")
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


# --- Foco del título y desplazamiento de la página de atrás ---


def contorno(page, selector):
    return page.evaluate(
        """(selector) => {
            const estilo = getComputedStyle(document.querySelector(selector));
            return { estilo: estilo.outlineStyle, ancho: estilo.outlineWidth };
        }""",
        selector,
    )


@pytest.mark.parametrize("tema", TEMAS)
def test_el_titulo_recibe_el_foco_sin_contorno_y_los_controles_si(portada, tema):
    portada.emulate_media(color_scheme=tema)
    abrir(portada)

    expect(portada.locator("#modal-titulo")).to_be_focused()
    assert portada.evaluate("document.getElementById('modal-titulo').tabIndex") == -1
    assert contorno(portada, "#modal-titulo")["estilo"] == "none"

    portada.keyboard.press("Tab")
    expect(dialogo(portada).get_by_role("button", name="Cerrar")).to_be_focused()
    assert contorno(portada, "#estudiantes [data-cerrar]") == {"estilo": "solid", "ancho": "2px"}

    portada.keyboard.press("Tab")
    expect(dialogo(portada).get_by_role("link", name="Agregar uno por uno")).to_be_focused()
    assert contorno(portada, "#estudiantes .boton-principal")["ancho"] == "2px"


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_portada_con_el_aviso_carga_empezando_arriba(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page.locator("#aviso-portada")).to_be_visible()
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)
    assert page.evaluate("window.scrollY") == 0

    page.goto(f"{live_server.url}/docente/")
    page.wait_for_timeout(300)
    assert page.evaluate("window.scrollY") == 0


@pytest.mark.parametrize("tema", TEMAS)
def test_cerrar_es_un_boton_con_borde_de_44_px_con_icono_y_texto(portada, tema):
    portada.emulate_media(color_scheme=tema)
    abrir(portada)

    cerrar = dialogo(portada).get_by_role("button", name="Cerrar")
    estilo = cerrar.evaluate(
        """(el) => {
            const e = getComputedStyle(el), secundario = document.createElement("a");
            secundario.className = "boton-secundario";
            document.body.append(secundario);
            const s = getComputedStyle(secundario);
            const datos = {
                alto: el.getBoundingClientRect().height,
                borde: e.borderTopWidth + " " + e.borderTopStyle,
                color: e.borderTopColor,
                colorSecundario: s.borderTopColor,
                radio: e.borderTopLeftRadius,
                radioSecundario: s.borderTopLeftRadius,
                icono: !!el.querySelector("svg.icono"),
            };
            secundario.remove();
            return datos;
        }"""
    )
    assert estilo["alto"] >= 44
    assert estilo["borde"] == "1px solid"
    assert estilo["color"] == estilo["colorSecundario"]
    assert estilo["radio"] == estilo["radioSecundario"]
    assert estilo["icono"]
    expect(cerrar).to_have_text("Cerrar")
