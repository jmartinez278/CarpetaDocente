"""Botón de tema en el navegador (T-04; spec pantallas-de-inicio «Temas claro y oscuro»; D1).

La elección se guarda y se aplica antes de pintar, sin pasar por el claro; sin elección el nombre
del botón sigue el cambio del sistema; la elección de una pestaña llega a las otras del contexto.
Necesita el CSS compilado y Chromium: ``uv run pytest -m e2e --browser chromium`` con
``DJANGO_ALLOW_ASYNC_UNSAFE=true``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import con_pantalla, ingresar

pytestmark = pytest.mark.e2e

# Anota cada cambio de data-theme con el estado del documento en ese momento. Corre en cada página
# nueva antes que cualquier otro script; se observa el documento y no <html>, que aún no existe.
REGISTRAR_TEMA = """(() => {
    window.__registro = [];
    new MutationObserver(() => {
        window.__registro.push([
            document.documentElement.getAttribute("data-theme"),
            document.readyState,
        ]);
    }).observe(document, { attributes: true, attributeFilter: ["data-theme"], subtree: true });
})()"""

A_OSCURO = "Cambiar a tema oscuro"
A_CLARO = "Cambiar a tema claro"


def abrir_portada(page, live_server, docente, clave, tema="light"):
    con_pantalla(page, 1280, tema)
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")


def boton(page, nombre):
    return page.get_by_role("button", name=nombre)


def tema_guardado(page):
    return page.evaluate("localStorage.getItem('tema')")


def test_la_eleccion_oscura_sobrevive_a_la_recarga_sin_pasar_por_el_claro(
    live_server, page, docente, clave
):
    page.add_init_script(REGISTRAR_TEMA)
    abrir_portada(page, live_server, docente, clave)

    boton(page, A_OSCURO).click()

    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(boton(page, A_CLARO)).to_be_visible()
    assert tema_guardado(page) == "dark"

    page.reload()

    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(boton(page, A_CLARO)).to_be_visible()
    # El único cambio de data-theme de la página recargada ocurrió con el documento aún cargándose:
    # antes de DOMContentLoaded y de pintar, sin pasar por el claro.
    assert page.evaluate("window.__registro") == [["dark", "loading"]]

    boton(page, A_CLARO).click()

    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(boton(page, A_OSCURO)).to_be_visible()
    assert tema_guardado(page) == "light"


def test_sin_eleccion_sigue_al_sistema_y_la_eleccion_llega_a_la_otra_pestana(
    live_server, page, docente, clave
):
    abrir_portada(page, live_server, docente, clave)
    expect(boton(page, A_OSCURO)).to_be_visible()

    page.emulate_media(color_scheme="dark")

    expect(boton(page, A_CLARO)).to_be_visible()
    assert page.evaluate("document.documentElement.hasAttribute('data-theme')") is False
    assert tema_guardado(page) is None

    page.emulate_media(color_scheme="light")
    expect(boton(page, A_OSCURO)).to_be_visible()

    otra = page.context.new_page()
    otra.goto(f"{live_server.url}/docente/")
    expect(boton(otra, A_OSCURO)).to_be_visible()

    boton(page, A_OSCURO).click()

    expect(otra.locator("html")).to_have_attribute("data-theme", "dark")
    expect(boton(otra, A_CLARO)).to_be_visible()
