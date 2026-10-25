"""Cierre de sesión en el navegador (spec cierre-sesion; design.md de US-002, D6).

Camino ideal, botón "atrás", inactividad, teclado, toque fuera y menú sin JavaScript. Necesita el
CSS compilado y Chromium: ``uv run pytest -m e2e --browser chromium`` con
``DJANGO_ALLOW_ASYNC_UNSAFE=true``.
"""

import re

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import envejecer_sesion, ingresar

pytestmark = pytest.mark.e2e

AVISO = "Tu sesión se cerró por inactividad."
DETALLE = "Pasaron 60 minutos sin uso. Ingresa de nuevo para continuar."


def boton_menu(page):
    # Playwright no da rol de botón al <summary>; se busca por su nombre accesible.
    return page.get_by_label("Menú de la cuenta")


def cerrar_sesion(page):
    return page.get_by_role("button", name="Cerrar sesión")


def menu_abierto(page):
    return page.locator("[data-menu-cuenta]")


def entrar_a_la_portada(page, live_server, docente, clave):
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    page.wait_for_load_state("load")


def test_camino_ideal_abre_el_menu_y_cierra_la_sesion(live_server, page, docente, clave):
    entrar_a_la_portada(page, live_server, docente, clave)

    boton_menu(page).click()
    expect(page.locator(".menu-cuenta__nombre")).to_have_text("Ana Quispe")
    cerrar_sesion(page).click()

    expect(page).to_have_url(f"{live_server.url}/ingresar/")
    expect(page.locator(".mensaje--aviso")).to_have_count(0)


def test_atras_despues_de_cerrar_sesion_no_muestra_el_saludo(live_server, page, docente, clave):
    entrar_a_la_portada(page, live_server, docente, clave)
    boton_menu(page).click()
    cerrar_sesion(page).click()
    expect(page).to_have_url(f"{live_server.url}/ingresar/")

    page.go_back()

    expect(page).to_have_url(f"{live_server.url}/ingresar/?next=/docente/")
    expect(page.get_by_text("Hola, Ana Quispe")).to_have_count(0)


def test_inactividad_muestra_el_aviso_y_atras_no_muestra_la_pantalla(
    live_server, page, docente, clave
):
    entrar_a_la_portada(page, live_server, docente, clave)
    # Una segunda entrada interna en el historial: "atrás" vuelve a una pantalla con sesión.
    page.goto(f"{live_server.url}/docente/?pagina=2")
    page.wait_for_load_state("load")
    envejecer_sesion(page, 61)

    page.reload()

    expect(page).to_have_url(re.compile(r"/ingresar/\?next=/docente/"))
    aviso = page.locator(".mensaje--aviso")
    expect(aviso).to_be_visible()
    expect(aviso).to_contain_text(AVISO)
    expect(aviso).to_contain_text(DETALLE)
    page.go_back()
    expect(page).to_have_url(f"{live_server.url}/ingresar/?next=/docente/")
    expect(page.get_by_text("Hola, Ana Quispe")).to_have_count(0)


def test_escape_cierra_el_menu_y_devuelve_el_foco(live_server, page, docente, clave):
    entrar_a_la_portada(page, live_server, docente, clave)
    boton_menu(page).focus()
    page.keyboard.press("Enter")
    expect(menu_abierto(page)).to_have_js_property("open", True)

    page.keyboard.press("Escape")

    expect(menu_abierto(page)).to_have_js_property("open", False)
    expect(boton_menu(page)).to_be_focused()


def test_un_toque_fuera_cierra_el_menu(live_server, page, docente, clave):
    entrar_a_la_portada(page, live_server, docente, clave)
    boton_menu(page).click()
    expect(menu_abierto(page)).to_have_js_property("open", True)

    page.get_by_role("heading", level=1).click()

    expect(menu_abierto(page)).to_have_js_property("open", False)


def test_sin_javascript_el_menu_abre_y_cierra_la_sesion(live_server, browser, docente, clave):
    contexto = browser.new_context(java_script_enabled=False)
    page = contexto.new_page()
    try:
        ingresar(page, live_server, docente, clave)
        expect(page).to_have_url(f"{live_server.url}/docente/")

        boton_menu(page).click()
        cerrar_sesion(page).click()

        expect(page).to_have_url(f"{live_server.url}/ingresar/")
    finally:
        contexto.close()


def restaurar_desde_bfcache(page):
    """Simula que "atrás" devuelve la pantalla guardada (``pageshow`` persistido)."""
    page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")


def entrar_al_panel(page, live_server, administrador, clave):
    ingresar(page, live_server, administrador, clave)
    page.goto(f"{live_server.url}/admin/")
    expect(page).to_have_url(f"{live_server.url}/admin/")
    page.wait_for_load_state("load")


def test_panel_atras_tras_el_cierre_manual_no_muestra_la_pantalla(
    live_server, page, administrador, clave
):
    entrar_al_panel(page, live_server, administrador, clave)
    # Otra pestaña cierra la sesión desde el panel; esta queda con la pantalla guardada.
    otra = page.context.new_page()
    otra.goto(f"{live_server.url}/admin/")
    otra.get_by_role("button", name=re.compile("cerrar sesión", re.IGNORECASE)).click()
    expect(otra).to_have_url(f"{live_server.url}/ingresar/")

    restaurar_desde_bfcache(page)

    expect(page).to_have_url(re.compile(r"/ingresar/\?next=/admin/"))
    page.go_back()
    expect(page.get_by_role("heading", name="Acciones recientes")).to_have_count(0)


def test_panel_atras_tras_la_inactividad_no_muestra_la_pantalla(
    live_server, page, administrador, clave
):
    entrar_al_panel(page, live_server, administrador, clave)
    envejecer_sesion(page, 61)

    restaurar_desde_bfcache(page)

    expect(page).to_have_url(re.compile(r"/ingresar/\?next=/admin/"))
    expect(page.locator(".mensaje--aviso")).to_contain_text(AVISO)
