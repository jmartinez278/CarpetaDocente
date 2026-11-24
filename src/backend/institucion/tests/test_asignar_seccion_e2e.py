"""Asignación de la sección en el navegador (spec asignacion-secciones; design.md de US-005, D7).

El Administrador asigna "2.º grado, sección A" en la ficha de la sección, la docente la ve bajo el
saludo y luego la misma sección no se puede asignar a otra docente. La portada con la línea de la
sección no desborda a 320 px; su axe va en la vista ``portada-una-seccion`` de
``test_accesibilidad_e2e``. Necesita el CSS compilado y Chromium; se
pide con ``uv run pytest -m e2e --browser chromium``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import con_pantalla, ingresar

pytestmark = pytest.mark.e2e

SECCION = "2.º grado, sección A"
# Desde US-040 la línea de la sección ya no lleva la fecha (la lleva la miniatura de Asistencia).
LINEA = SECCION
OCUPADA = "La sección ya tiene un docente asignado"


def asignar_en_la_ficha(page, live_server, seccion, docente):
    page.goto(f"{live_server.url}/admin/institucion/seccion/{seccion.pk}/change/")
    page.get_by_label("Docente de aula").select_option(str(docente.pk))
    page.get_by_role("button", name="Guardar", exact=True).click()


def test_el_administrador_asigna_la_seccion_y_la_docente_la_ve(
    live_server, browser, page, administrador, seccion, docente, otra_docente, clave
):
    ingresar(page, live_server, administrador, clave)
    expect(page).to_have_url(f"{live_server.url}/admin/")

    asignar_en_la_ficha(page, live_server, seccion, docente)
    expect(page.locator(".messagelist")).to_be_visible()

    # La docente ingresa desde otro navegador.
    contexto = browser.new_context()
    portada = contexto.new_page()
    try:
        ingresar(portada, live_server, docente, clave)
        expect(portada).to_have_url(f"{live_server.url}/docente/")
        expect(portada.locator(".seccion-entrada p")).to_have_text(LINEA)
        expect(portada.locator("h1")).not_to_contain_text(SECCION)
    finally:
        contexto.close()

    asignar_en_la_ficha(page, live_server, seccion, otra_docente)
    expect(page.locator(".errorlist")).to_contain_text(OCUPADA)
    seccion.refresh_from_db()
    assert seccion.docente == docente


@pytest.fixture
def docente_con_seccion(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return docente


def test_la_portada_con_la_seccion_no_desborda_a_320_px(
    live_server, page, docente_con_seccion, clave
):
    con_pantalla(page, 320, "light")
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page.locator(".seccion-entrada p")).to_have_text(LINEA)
    page.evaluate("document.fonts.ready")

    assert page.evaluate("document.documentElement.scrollWidth") <= 320
