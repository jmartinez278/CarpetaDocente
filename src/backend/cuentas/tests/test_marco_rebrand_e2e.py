"""Marco del rebrand en el navegador, sobre «sin permiso» (specs pantallas-de-inicio y
cierre-sesion; rebrand-base, D4, D5, D7 y D9).

Barra, pie, ☰ (diálogo con JS, enlace sin JS) y menú de la cuenta. Necesita el CSS compilado y
Chromium: ``uv run pytest -m e2e --browser chromium`` con ``DJANGO_ALLOW_ASYNC_UNSAFE=true``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import TEMAS, con_pantalla, ingresar
from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.e2e

SIN_PERMISO = "/docente/sin-permiso/"


@pytest.fixture
def con_seccion(docente, institucion):
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2027)
    return Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)


def entrar(page, live_server, docente, clave, ruta=SIN_PERMISO):
    ingresar(page, live_server, docente, clave)
    page.wait_for_url("**/docente/")
    if ruta != "/docente/":
        page.goto(f"{live_server.url}{ruta}")
    page.wait_for_load_state("load")
    page.evaluate("document.fonts.ready")


def boton_menu(page):
    return page.locator("[data-menu-navegacion]")


def dialogo(page):
    return page.locator("dialog#navegacion")


def cerrar_navegacion(page):
    return page.get_by_role("button", name="Cerrar navegación")


def cuenta(page):
    return page.locator("[data-menu-cuenta]")


def boton_cuenta(page):
    # Playwright no da rol de botón al <summary>; se busca por su nombre accesible.
    return page.get_by_label("Menú de la cuenta")


def foco_en(page, selector):
    return page.evaluate(f"document.activeElement === document.querySelector('{selector}')")


def abrir_navegacion(page):
    boton_menu(page).click()
    expect(dialogo(page)).to_have_js_property("open", True)
    # Se mide con el panel ya en su lugar, no a mitad de la entrada.
    page.wait_for_function("document.getAnimations().length === 0")


def esperar_cierre(page):
    expect(dialogo(page)).to_have_js_property("open", False)
    expect(boton_menu(page)).to_have_attribute("aria-expanded", "false")
    page.wait_for_function(
        "document.activeElement === document.querySelector('[data-menu-navegacion]')"
    )


# --- Barra y pie (spec pantallas-de-inicio, «Marco común») ---


@pytest.mark.parametrize(("ancho", "alto"), [(1280, 72), (360, 64)])
def test_barra_de_una_pantalla_interior(live_server, page, docente, clave, ancho, alto):
    con_pantalla(page, ancho, "light")
    entrar(page, live_server, docente, clave)

    barra = page.locator("header.appbar")
    expect(barra.locator(".bar-title")).to_have_text("Sin permiso")
    assert barra.bounding_box()["height"] == alto

    # Contenido de más para que la página se desplace: la barra sigue arriba.
    page.evaluate("document.body.style.minHeight = '4000px'")
    page.mouse.wheel(0, 1500)
    page.wait_for_function("window.scrollY > 1000")
    assert barra.bounding_box()["y"] == 0


@pytest.mark.parametrize("ancho", [1280, 360])
def test_pie_alineado_con_el_contenido(live_server, page, docente, clave, ancho):
    con_pantalla(page, ancho, "light")
    entrar(page, live_server, docente, clave)

    contenido = page.locator("main").bounding_box()
    izquierda = page.get_by_text("CarpetaDocente · 2026").bounding_box()
    derecha = page.locator("footer").get_by_text("I.E. Virgen del Carmen").bounding_box()

    assert izquierda["x"] == pytest.approx(contenido["x"], abs=1)
    assert derecha["x"] + derecha["width"] == pytest.approx(
        contenido["x"] + contenido["width"], abs=1
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


# --- ☰ (requisito «Navegación de la docente») ---


def test_abrir_el_menu(live_server, page, docente, clave, con_seccion):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)

    expect(page.get_by_role("button", name="Menú de navegación")).to_have_attribute(
        "aria-expanded", "false"
    )
    abrir_navegacion(page)

    expect(boton_menu(page)).to_have_attribute("aria-expanded", "true")
    assert dialogo(page).evaluate("(d) => d.matches(':modal')")
    # El panel cubre la barra: lo que se ve arriba a la izquierda es el diálogo.
    assert page.evaluate(
        "document.querySelector('dialog#navegacion').contains(document.elementFromPoint(40, 20))"
    )
    nav = page.get_by_role("navigation", name="Navegación principal")
    expect(nav.get_by_role("link")).to_have_text(["Inicio", "Asistencia", "Notas"])
    expect(nav.get_by_text("Próximamente")).to_have_count(1)
    expect(cerrar_navegacion(page)).to_be_visible()


def test_teclado_no_sale_del_dialogo_y_escape_devuelve_el_foco(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)

    boton_menu(page).focus()
    page.keyboard.press("Enter")
    expect(dialogo(page)).to_have_js_property("open", True)
    # Tras el último control, Chrome lleva el foco a su propia interfaz (body), no a la página.
    for _ in range(8):
        page.keyboard.press("Tab")
        assert page.evaluate(
            """() => document.activeElement === document.body
                || document.querySelector('dialog#navegacion').contains(document.activeElement)"""
        )

    page.keyboard.press("Escape")

    esperar_cierre(page)


def test_cerrar_con_la_x(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)
    abrir_navegacion(page)

    cerrar_navegacion(page).click()

    esperar_cierre(page)


def test_toque_fuera_del_panel(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)
    abrir_navegacion(page)

    page.mouse.click(900, 400)

    esperar_cierre(page)


def test_sin_javascript_el_menu_lleva_a_la_portada(live_server, browser, docente, clave):
    contexto = browser.new_context(java_script_enabled=False)
    page = contexto.new_page()
    try:
        entrar(page, live_server, docente, clave)

        enlace = page.get_by_role("link", name="Inicio", exact=True)
        expect(enlace).to_have_attribute("data-menu-navegacion", "")
        enlace.click()

        page.wait_for_url(f"{live_server.url}/docente/")
    finally:
        contexto.close()


@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("tema", TEMAS)
def test_menu_abierto_no_desborda(live_server, page, docente, clave, tema, ancho):
    con_pantalla(page, ancho, tema)
    entrar(page, live_server, docente, clave)
    abrir_navegacion(page)

    caja = cerrar_navegacion(page).bounding_box()
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    assert caja["x"] >= 0
    assert caja["x"] + caja["width"] <= ancho
    expect(cerrar_navegacion(page)).to_be_in_viewport()


def test_abrir_el_menu_cierra_la_cuenta(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)
    boton_cuenta(page).click()
    expect(cuenta(page)).to_have_js_property("open", True)

    abrir_navegacion(page)

    expect(cuenta(page)).to_have_js_property("open", False)


# --- Cuenta (spec cierre-sesion, «Menú de la cuenta») ---


def test_abrir_la_cuenta(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)

    boton_cuenta(page).click()

    panel = page.locator("[data-cuenta-panel]")
    expect(panel).to_be_visible()
    expect(panel.locator("p")).to_have_text(["Tu cuenta", "Ana Quispe", "I.E. Virgen del Carmen"])
    expect(panel.get_by_role("button", name="Cerrar sesión")).to_be_visible()


def test_la_cuenta_con_seccion(live_server, page, docente, clave, con_seccion):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)

    boton_cuenta(page).click()

    expect(page.locator("[data-cuenta-panel]").get_by_text("2.º grado, sección A")).to_be_visible()


def test_la_cuenta_con_teclado(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)

    boton_cuenta(page).focus()
    page.keyboard.press("Enter")
    expect(cuenta(page)).to_have_js_property("open", True)
    page.keyboard.press("Escape")

    expect(cuenta(page)).to_have_js_property("open", False)
    assert foco_en(page, "[data-menu-cuenta] summary")


def test_toque_fuera_de_la_cuenta(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)
    boton_cuenta(page).click()

    page.mouse.click(400, 500)

    expect(cuenta(page)).to_have_js_property("open", False)


def test_sin_javascript_la_cuenta_abre_y_cierra_la_sesion(live_server, browser, docente, clave):
    contexto = browser.new_context(java_script_enabled=False)
    page = contexto.new_page()
    try:
        entrar(page, live_server, docente, clave)

        boton_cuenta(page).click()
        page.get_by_role("button", name="Cerrar sesión").click()

        page.wait_for_url(f"{live_server.url}/ingresar/")
    finally:
        contexto.close()


@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("tema", TEMAS)
def test_cuenta_abierta_no_desborda(live_server, page, docente, clave, tema, ancho):
    con_pantalla(page, ancho, tema)
    entrar(page, live_server, docente, clave)
    boton_cuenta(page).click()

    panel = page.locator("[data-cuenta-panel]").bounding_box()
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    assert panel["x"] >= 0
    assert panel["x"] + panel["width"] <= ancho


# --- Una hoja por página (D9) ---


HOJAS = (
    "[...document.querySelectorAll('link[rel=stylesheet]')].map((l) => new URL(l.href).pathname)"
)


@pytest.mark.parametrize(
    ("ruta", "hoja"),
    [(SIN_PERMISO, "/static/dist/rebrand.css"), ("/docente/", "/static/dist/app.css")],
)
def test_cada_pagina_carga_una_sola_hoja(live_server, page, docente, clave, ruta, hoja):
    entrar(page, live_server, docente, clave, ruta)

    assert page.evaluate(HOJAS) == [hoja]


# --- Movimiento (DESIGN.md, Movimiento y sus 4 reglas; D5) ---


def estilo(page, selector, propiedad):
    return page.evaluate(
        "([s, p]) => getComputedStyle(document.querySelector(s))[p]", [selector, propiedad]
    )


@pytest.mark.parametrize("movimiento", ["no-preference", "reduce"])
def test_e02_el_foco_aparece_de_una_vez(live_server, page, docente, clave, movimiento):
    con_pantalla(page, 1280, "light")
    page.emulate_media(reduced_motion=movimiento)
    entrar(page, live_server, docente, clave)

    # «Ir al contenido», luego el ☰ y luego la cuenta.
    for selector in ("[data-menu-navegacion]", "[data-menu-cuenta] summary"):
        page.keyboard.press("Tab")
        while not foco_en(page, selector):
            page.keyboard.press("Tab")
        assert page.evaluate("document.getAnimations().length") == 0
        assert estilo(page, selector, "outlineOffset") == "4px"
        assert estilo(page, selector, "outlineStyle") == "solid"
        assert "outline" not in estilo(page, selector, "transitionProperty")


CERRAR_A_MEDIA_ENTRADA = """async () => {
  const boton = document.querySelector("[data-menu-navegacion]");
  const panel = document.getElementById("navegacion");
  boton.click();
  await new Promise((listo) => setTimeout(listo, 90));
  const antes = getComputedStyle(panel).transform;
  // Escape llega al <dialog> como «cancel».
  panel.dispatchEvent(new Event("cancel", { cancelable: true }));
  const despues = getComputedStyle(panel).transform;
  return { antes, despues, abierto: panel.open };
}"""


def desplazamiento(matriz):
    """El ``translateX`` de una ``matrix(a, b, c, d, tx, ty)``; 0 sin transformación."""
    return 0.0 if matriz == "none" else float(matriz[7:-1].split(",")[4])


def test_e03_cerrar_a_media_entrada_sigue_desde_donde_esta(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)

    medida = page.evaluate(CERRAR_A_MEDIA_ENTRADA)

    assert desplazamiento(medida["antes"]) < 0, "a los 90 ms el panel todavía está entrando"
    assert desplazamiento(medida["despues"]) == pytest.approx(
        desplazamiento(medida["antes"]), abs=1
    )
    assert medida["abierto"], "el diálogo sigue abierto mientras sale"
    esperar_cierre(page)


def test_e05_la_pulsacion_solo_con_el_mouse(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, docente, clave)
    selector = "[data-menu-cuenta] summary"
    page.mouse.move(640, 600)

    page.locator(selector).focus()
    page.keyboard.down("Space")
    con_teclado = estilo(page, selector, "transform")
    page.keyboard.up("Space")
    page.keyboard.press("Escape")

    caja = page.locator(selector).bounding_box()
    page.mouse.move(caja["x"] + caja["width"] / 2, caja["y"] + caja["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(150)
    con_mouse = estilo(page, selector, "transform")
    page.mouse.up()

    assert con_teclado == "none"
    assert con_mouse != "none"


def test_movimiento_reducido_el_menu_no_se_desplaza(live_server, page, docente, clave):
    con_pantalla(page, 1280, "light")
    page.emulate_media(reduced_motion="reduce")
    entrar(page, live_server, docente, clave)

    medida = page.evaluate(CERRAR_A_MEDIA_ENTRADA)

    assert medida["antes"] == "none"
    assert medida["despues"] == "none"
    assert not medida["abierto"], "con movimiento reducido el cierre es inmediato"
    esperar_cierre(page)
