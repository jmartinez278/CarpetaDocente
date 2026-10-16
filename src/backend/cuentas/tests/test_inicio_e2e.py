"""Prueba de punta a punta de la página inicial (spec integracion-continua, EN-08).

Abre la página en Chromium contra el servidor de ``live_server`` y comprueba lo que
``test_inicio.py`` no ve en el HTML: que la hoja de estilos compilada carga y que
HTMX y Alpine.js se ejecutan. Necesita el CSS compilado (``npm run build`` en
``src/frontend/``) y Chromium (``uv run playwright install chromium``); se pide con
``uv run pytest -m e2e --browser chromium``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.tests.test_inicio import DIMENSIONES

pytestmark = pytest.mark.e2e


@pytest.fixture
def respuesta_css(live_server, page):
    """Abre la página inicial y devuelve la respuesta a la hoja de estilos que pidió."""
    with page.expect_response("**/static/dist/app.css") as respuesta:
        page.goto(live_server.url)
    return respuesta.value


def test_muestra_el_nombre_y_las_tres_dimensiones_en_orden(respuesta_css, page):
    expect(page.get_by_role("heading", level=1)).to_have_text("CarpetaDocente")
    expect(page.get_by_role("listitem")).to_have_text(DIMENSIONES)


def test_la_hoja_de_estilos_carga(respuesta_css):
    assert respuesta_css.status == 200


@pytest.mark.parametrize("libreria", ["htmx", "Alpine"])
def test_htmx_y_alpine_estan_disponibles(respuesta_css, page, libreria):
    assert page.evaluate(f"typeof {libreria}") != "undefined"
