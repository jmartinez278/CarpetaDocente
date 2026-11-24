"""La portada de la dirección y su ☰ en el navegador (US-040, D11; spec pantallas-de-inicio).

Axe y ancho del documento de la portada, con y sin bimestres, y del ☰ de la dirección abierto, y
de Consolidados y del detalle de una sección (Notas, Pendientes, Asistencia y Sesiones), en tema
claro y oscuro a 360 px; y el recorrido de la portada a la página de una sesión. Necesita
el CSS compilado y Chromium: ``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser
chromium src/backend/direccion/tests/test_direccion_e2e.py``.
"""

import re
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import TEMAS, con_pantalla, fijar_hora_de_lima, ingresar, revisar_con_axe
from direccion.tests.conftest import crear_seccion
from notas.tests.conftest import MATEMATICA, ids_de, marcar, poner_nota

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


# --- Consolidados y detalle de una sección (7.2; spec consolidados-direccion) ---

ENVIADA = datetime(2027, 11, 18, 10, 0, tzinfo=ZoneInfo("America/Lima"))


@pytest.fixture
def con_de_todo(veinticuatro, bimestres, docente, crear_sesion):
    """2.º A con una nota pendiente en Matemática, la asistencia completa y una sesión.

    Matemática lleva 4 competencias: el primer estudiante tiene todas sus notas y el segundo,
    ninguna; faltan 4. Con ``veinticuatro``, 2.º A es la quinta sección.
    """
    seccion = veinticuatro[4]
    cuarto = bimestres[3]
    marcar(seccion, cuarto, ids_de(MATEMATICA))
    primero = seccion.estudiantes.order_by("pk").first()
    for competencia_id in ids_de(MATEMATICA):
        poner_nota(primero, competencia_id, cuarto, "A")
    crear_sesion(docente, creado_en=ENVIADA, titulo="Contamos objetos del aula")
    return seccion


def url_detalle(nombre, seccion, **consulta):
    return f"/direccion/consolidados/secciones/{seccion.pk}/{nombre}/" + (
        f"?{urlencode(consulta)}" if consulta else ""
    )


def test_el_recorrido_de_la_direccion_de_la_portada_a_una_sesion(
    live_server, page, direccion, clave, con_de_todo
):
    """Flujo principal: portada, banda, Consolidados, 2.º A, Notas, Pendientes, Asistencia,
    Sesiones y la página de una sesión (spec consolidados-direccion, «Camino ideal»)."""
    con_pantalla(page, 1280, "light")
    entrar(page, live_server, direccion, clave)

    page.get_by_role("link", name="Consolidados").first.click()
    expect(page).to_have_url(re.compile(r"/direccion/consolidados/$"))
    expect(page.get_by_role("heading", level=1)).to_have_text("Consolidados")

    page.get_by_role("link", name=re.compile(r"^A de 2\.º")).click()
    expect(page).to_have_url(re.compile(r"/notas/\?periodo=4$"))
    expect(page.get_by_role("heading", level=1)).to_have_text("2.º grado, sección A")
    expect(page.get_by_role("link", name="Notas")).to_have_attribute("aria-current", "page")

    page.get_by_role("link", name=re.compile(r"^Pendientes")).click()
    expect(page.get_by_role("heading", name="Pendientes · Matemática")).to_be_visible()
    expect(page.get_by_role("link", name=re.compile(r"^Pendientes"))).to_have_attribute(
        "aria-current", "page"
    )

    page.get_by_role("link", name="Asistencia").click()
    expect(page.get_by_role("heading", name="Totales por estudiante")).to_be_visible()

    page.get_by_role("link", name="Sesiones").click()
    expect(page.get_by_role("heading", name=re.compile(r"^Semana del"))).to_be_visible()
    page.get_by_role("link", name=re.compile("Contamos objetos del aula")).click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Contamos objetos del aula")
    expect(page.get_by_role("link", name="Descargar")).to_be_visible()
    expect(page.get_by_role("button", name="Eliminar")).to_have_count(0)


PANTALLAS = {
    "consolidados": lambda s: CONSOLIDADOS,
    "notas": lambda s: url_detalle("notas", s, periodo=4, area=MATEMATICA),
    "pendientes": lambda s: url_detalle(
        "notas", s, periodo=4, area=MATEMATICA, filtro="pendientes"
    ),
    "asistencia": lambda s: url_detalle("asistencia", s, periodo=4),
    "sesiones": lambda s: url_detalle("sesiones", s, periodo=4),
}


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("pantalla", PANTALLAS)
def test_consolidados_y_el_detalle_pasan_axe_y_no_se_desplazan_en_horizontal(
    live_server, page, tema, pantalla, direccion, clave, con_de_todo
):
    """Escenario «Revisión de Consolidados y del detalle»: a 360 px, en ambos temas."""
    con_pantalla(page, ANCHO, tema)

    entrar(page, live_server, direccion, clave, ruta=PANTALLAS[pantalla](con_de_todo))

    expect(page.get_by_role("heading", level=1)).to_be_visible()
    assert ancho_del_documento(page) <= ANCHO
    revisar_con_axe(page, f"direccion-{pantalla}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
def test_6d_sin_estudiantes_pasa_axe_y_no_se_desplaza_en_horizontal(
    live_server, page, tema, direccion, clave, veinticuatro
):
    con_pantalla(page, ANCHO, tema)

    entrar(page, live_server, direccion, clave, ruta=url_detalle("sesiones", veinticuatro[-1]))

    expect(
        page.get_by_text("Sin estudiantes: no hay notas ni asistencia que sumar.")
    ).to_be_visible()
    assert ancho_del_documento(page) <= ANCHO
    revisar_con_axe(page, f"direccion-6d-{tema}")
