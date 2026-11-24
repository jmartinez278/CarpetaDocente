"""La portada de la dirección y su ☰ en el navegador (US-040, D11; spec pantallas-de-inicio).

Axe y ancho del documento de la portada, con y sin bimestres, y del ☰ de la dirección abierto, en
tema claro y oscuro a 360 px. El flujo de Consolidados y el detalle se suma en el grupo 7. Necesita
el CSS compilado y Chromium: ``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser
chromium src/backend/direccion/tests/test_direccion_e2e.py``.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import TEMAS, con_pantalla, fijar_hora_de_lima, ingresar, revisar_con_axe
from direccion.tests.conftest import crear_seccion

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

# El lunes 22 de noviembre de 2027, 9:00 de Lima, en el IV bimestre de la fixture ``bimestres``.
MOMENTO = datetime(2027, 11, 22, 9, 0, tzinfo=ZoneInfo("America/Lima"))
ANCHO = 360
INICIO = "/direccion/"
CONSOLIDADOS = "/direccion/consolidados/"


@pytest.fixture(autouse=True)
def _catalogo_y_reloj(catalogo, monkeypatch):
    """El catálogo debe estar antes de crear la institución, que copia sus áreas."""
    fijar_hora_de_lima(monkeypatch, MOMENTO)


def entrar(page, live_server, direccion, clave, ruta=INICIO):
    ingresar(page, live_server, direccion, clave)
    page.wait_for_url(f"**{INICIO}")
    if ruta != INICIO:
        page.goto(f"{live_server.url}{ruta}")
    page.wait_for_load_state("load")
    page.evaluate("document.fonts.ready")
    # axe mide el color calculado: a media transición lo mezcla con la opacidad.
    page.wait_for_function("document.getAnimations().length === 0")


def ancho_del_documento(page):
    return page.evaluate("document.documentElement.scrollWidth")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("bimestres_configurados", [True, False], ids=["con-bimestres", "sin"])
def test_la_portada_de_la_direccion_pasa_axe_y_no_se_desplaza_en_horizontal(
    live_server,
    page,
    request,
    tema,
    bimestres_configurados,
    direccion,
    clave,
    anio_abierto,
    docente,
):
    """Escenarios «Pantallas de US-040», «Inicio de la dirección en el Sprint 1» y «Sin bimestres
    en la portada»."""
    if bimestres_configurados:
        request.getfixturevalue("veinticuatro")
    else:
        crear_seccion(anio_abierto, 2, "A", docente=docente, estudiantes=2)
    con_pantalla(page, ANCHO, tema)

    entrar(page, live_server, direccion, clave)

    expect(page.get_by_role("heading", level=1)).to_contain_text("Luisa Huamán")
    if bimestres_configurados:
        expect(page.get_by_text("13 secciones por revisar")).to_be_visible()
    else:
        expect(page.get_by_text("Aún no hay bimestres configurados")).to_be_visible()
    assert ancho_del_documento(page) <= ANCHO
    revisar_con_axe(page, f"direccion-portada-{'con' if bimestres_configurados else 'sin'}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
def test_el_menu_de_la_direccion_abierto_pasa_axe_y_cabe_en_la_ventana(
    live_server, page, tema, direccion, clave, veinticuatro
):
    """Escenarios «Abrir el ☰ de la dirección» y «Ubicación actual en el detalle»."""
    con_pantalla(page, ANCHO, tema)
    entrar(page, live_server, direccion, clave, ruta=CONSOLIDADOS)

    page.get_by_role("button", name="Menú de navegación").click()

    panel = page.locator("dialog#navegacion")
    expect(panel).to_have_js_property("open", True)
    expect(panel.get_by_role("link")).to_have_text(["Inicio", "Consolidados"])
    expect(panel.get_by_role("link", name="Consolidados")).to_have_attribute("aria-current", "page")
    expect(panel.get_by_text("Entregas")).to_be_visible()
    expect(panel.get_by_text("Próximamente")).to_be_visible()
    page.wait_for_function("document.getAnimations().length === 0")
    assert ancho_del_documento(page) <= ANCHO
    caja = panel.bounding_box()
    assert caja["x"] >= 0
    assert caja["x"] + caja["width"] <= ANCHO
    revisar_con_axe(page, f"direccion-menu-abierto-{tema}")
