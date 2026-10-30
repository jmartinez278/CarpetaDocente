"""Registro de actividad en el navegador (spec registro-actividad; design de US-008, D9 y D10).

La lista del registro y "Indicadores por semana" pasan axe en ambos temas a 360 y 1280 px, y el
botón "Exportar CSV" descarga lo que la lista tiene filtrado. Necesita el CSS compilado y Chromium:
``uv run pytest -m e2e --browser chromium``.
"""

import csv
import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from playwright.sync_api import expect

from actividad.models import Operacion, RegistroActividad
from actividad.tests.conftest import quitar_inicio_de_sesion
from actividad.tests.test_panel import entrada
from cuentas.tests.e2e import ANCHOS, TEMAS, con_pantalla, ingresar, revisar_con_axe

pytestmark = pytest.mark.e2e

LISTA = "/admin/actividad/registroactividad/"
INDICADORES = f"{LISTA}indicadores/"
MARTES = datetime(2026, 10, 27, 15, 0, tzinfo=UTC)


@pytest.fixture
def con_entradas(docente):
    """Dos entradas de operaciones distintas, para que el filtro deje fuera una."""
    entrada(
        docente,
        Operacion.REGISTRO_ASISTENCIA,
        MARTES,
        entidad="jornada",
        entidad_id=7,
        detalle={"seccion": 3, "fecha": "2026-10-27"},
    )
    entrada(docente, Operacion.INICIO_SESION, MARTES)


@pytest.fixture
def en_el_panel(live_server, page, administrador, clave):
    ingresar(page, live_server, administrador, clave)
    expect(page).to_have_url(f"{live_server.url}/admin/")
    quitar_inicio_de_sesion(administrador)
    return page


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_la_lista_del_registro_pasa_axe(live_server, en_el_panel, con_entradas, tema, ancho):
    con_pantalla(en_el_panel, ancho, tema)
    en_el_panel.goto(f"{live_server.url}{LISTA}")
    expect(en_el_panel.locator("#result_list tbody tr")).to_have_count(2)

    revisar_con_axe(en_el_panel, f"registro-actividad-{tema}-{ancho}")


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_los_indicadores_por_semana_pasan_axe(live_server, en_el_panel, con_entradas, tema, ancho):
    con_pantalla(en_el_panel, ancho, tema)
    en_el_panel.goto(f"{live_server.url}{LISTA}")
    en_el_panel.get_by_role("link", name="Indicadores por semana").click()
    expect(en_el_panel).to_have_url(f"{live_server.url}{INDICADORES}")
    # #content-main: el menú lateral del panel también tiene tablas, ocultas en el celular.
    expect(en_el_panel.locator("#content-main tbody tr").first).to_be_visible()

    revisar_con_axe(en_el_panel, f"indicadores-semana-{tema}-{ancho}")


@pytest.mark.parametrize("ruta", [LISTA, INDICADORES])
@pytest.mark.parametrize("tema", TEMAS)
def test_las_pantallas_no_desbordan_a_360_px(live_server, en_el_panel, con_entradas, tema, ruta):
    con_pantalla(en_el_panel, 360, tema)
    en_el_panel.goto(f"{live_server.url}{ruta}")
    expect(en_el_panel.locator("#content-main")).to_be_visible()
    en_el_panel.evaluate("document.fonts.ready")

    assert en_el_panel.evaluate("document.documentElement.scrollWidth") <= 360


def test_el_boton_descarga_el_csv_de_lo_filtrado(live_server, en_el_panel, con_entradas):
    en_el_panel.goto(f"{live_server.url}{LISTA}?operacion__exact={Operacion.REGISTRO_ASISTENCIA}")
    expect(en_el_panel.locator("#result_list tbody tr")).to_have_count(1)

    with en_el_panel.expect_download() as descarga:
        en_el_panel.get_by_role("button", name="Exportar CSV").click()
    archivo = descarga.value

    assert archivo.suggested_filename.startswith("registro-actividad-")
    assert archivo.suggested_filename.endswith(".csv")
    contenido = Path(archivo.path()).read_bytes()
    assert contenido.startswith(b"\xef\xbb\xbf")
    filas = list(csv.reader(io.StringIO(contenido.decode("utf-8-sig"))))
    assert len(filas) == 2  # encabezado y la única fila filtrada
    assert filas[1][1:5] == ["aquispe", Operacion.REGISTRO_ASISTENCIA, "jornada", "7"]

    exportada = RegistroActividad.objects.get(operacion=Operacion.REGISTRO_EXPORTADO)
    assert exportada.detalle == {
        "filtros": {"operacion__exact": Operacion.REGISTRO_ASISTENCIA},
        "filas": 1,
    }
