"""Accesibilidad con axe-core en las pantallas de US-001 y US-002 (spec pantallas-de-inicio; D10).

Las vistas (inicio de sesión normal, con error, con campos vacíos, «Ingresando…» y con el aviso
de inactividad; portada y dirección, cada una con el menú cerrado y abierto; «sin permiso») en
tema claro y oscuro, a 360 y 1280 px. Falla ante infracciones ``critical`` o ``serious`` de WCAG 2.1
A y AA, el contraste incluido (RNF-008), y guarda el informe en ``test-results/``. axe-core llega
por npm (``npm ci`` en ``src/frontend/``). Se pide con ``uv run pytest -m e2e --browser chromium``.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    abrir_ingresar,
    boton_ingresar,
    campo_clave,
    campo_usuario,
    con_pantalla,
    envejecer_sesion,
    fijar_hora_de_lima,
    ingresar,
    revisar_con_axe,
)
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.e2e

MIERCOLES_9 = datetime(2026, 10, 28, 9, 0, tzinfo=ZoneInfo("America/Lima"))

VISTAS = [
    "ingresar",
    "ingresar-con-error",
    "ingresar-vacio",
    "ingresar-enviando",
    "ingresar-con-aviso",
    "portada",
    "portada-una-seccion",
    "portada-varias-secciones",
    "portada-sin-estudiantes",
    "portada-hoy-pendiente",
    "portada-proximamente",
    "portada-menu-abierto",
    "portada-dialogo-estudiantes",
    "direccion",
    "direccion-menu-abierto",
    "sin-permiso",
    "sin-permiso-menu-abierto",
    "sin-permiso-cuenta-abierta",
]


def abrir_vista(page, live_server, vista, docente, direccion, clave):
    if vista == "ingresar":
        abrir_ingresar(page, live_server)
    elif vista == "ingresar-con-error":
        abrir_ingresar(page, live_server)
        campo_usuario(page).fill(docente.username)
        campo_clave(page).fill(f"{clave}-incorrecta")
        boton_ingresar(page).click()
        page.locator(".message--error").wait_for()
    elif vista == "ingresar-vacio":
        abrir_ingresar(page, live_server)
        boton_ingresar(page).click()
        page.locator(".field-error").first.wait_for()
    elif vista == "ingresar-enviando":
        # El envío retenido (como en test_ingresar_e2e): «Ingresando…» se queda en pantalla.
        abrir_ingresar(page, live_server)
        page.evaluate(
            "document.querySelector('[data-formulario-ingreso]')"
            ".addEventListener('submit', (evento) => evento.preventDefault())"
        )
        campo_usuario(page).fill(docente.username)
        campo_clave(page).fill(clave)
        boton_ingresar(page).click()
        page.get_by_role("button", name="Ingresando…").wait_for()
    elif vista == "ingresar-con-aviso":
        ingresar(page, live_server, docente, clave)
        page.wait_for_url("**/docente/")
        envejecer_sesion(page, 61)
        page.reload()
        page.locator(".message--aviso").wait_for()
        # axe mide el color calculado: a media animación de entrada lo mezcla con la opacidad.
        page.wait_for_function("document.getAnimations().length === 0")
    elif vista.startswith("sin-permiso"):
        ingresar(page, live_server, docente, clave)
        page.wait_for_url("**/docente/")
        page.goto(f"{live_server.url}/docente/sin-permiso/")
        page.get_by_role("heading", name="No tienes permiso para ver esta sección").wait_for()
        page.wait_for_load_state("load")
        if vista == "sin-permiso-menu-abierto":
            page.get_by_role("button", name="Menú de navegación").click()
            expect(page.locator("dialog#navegacion")).to_have_js_property("open", True)
        elif vista == "sin-permiso-cuenta-abierta":
            page.get_by_label("Menú de la cuenta").click()
            page.locator("[data-cuenta-panel]").wait_for()
        # axe mide el color calculado: a media transición lo mezcla con la opacidad.
        page.wait_for_function("document.getAnimations().length === 0")
    else:
        es_portada = vista.startswith("portada")
        if es_portada:
            preparar_portada(vista, docente)
        ingresar(page, live_server, docente if es_portada else direccion, clave)
        page.wait_for_url(f"**/{'docente' if es_portada else 'direccion'}/")
        page.wait_for_load_state("load")
        if vista.endswith("-menu-abierto"):
            page.get_by_label("Menú de la cuenta").click()
            page.locator("[data-cuenta-panel]").wait_for()
        elif vista == "portada-proximamente":
            # force: Playwright no da por habilitado un botón con aria-disabled.
            page.get_by_role("button", name="Sesiones", exact=True).click(force=True)
            expect(page.locator("#c-sesiones .dimension-aviso")).to_have_text(
                "Llegará en una próxima versión."
            )
        elif vista == "portada-dialogo-estudiantes":
            page.get_by_role("link", name="Ver estudiantes").click()
            expect(page.locator("dialog#estudiantes")).to_have_js_property("open", True)
            page.locator("#modal-titulo").wait_for()
        # axe mide el color calculado: a media transición lo mezcla con la opacidad.
        page.wait_for_function("document.getAnimations().length === 0")


def preparar_portada(vista, docente):
    """Secciones y estudiantes de cada vista de la portada (escenario «Revisión de cada pantalla»).

    Con una sección y estudiantes, la prueba fija un miércoles a las 9:00 de Lima: la jornada está
    sin completar y la tarjeta Asistencia lleva «Hoy: pendiente».
    """
    secciones = {
        "portada-una-seccion": [(2, "A")],
        "portada-varias-secciones": [(2, "A"), (3, "B")],
        "portada-sin-estudiantes": [(2, "A")],
        "portada-hoy-pendiente": [(2, "A")],
        "portada-proximamente": [(2, "A")],
        "portada-menu-abierto": [(2, "A")],
        "portada-dialogo-estudiantes": [(2, "A")],
    }.get(vista, [])
    if not secciones:
        return
    anio = AnioEscolar.objects.create(institucion=docente.institucion, anio=2027)
    for grado, nombre in secciones:
        seccion = Seccion.objects.create(
            anio_escolar=anio, grado=grado, nombre=nombre, docente=docente
        )
        if vista == "portada-sin-estudiantes":
            continue
        for apellidos in ("AGUILAR FLORES", "BRAVO CASAS", "CRUZ HUAMÁN"):
            Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres="ANA")


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("vista", VISTAS)
def test_sin_infracciones_graves_de_accesibilidad(
    live_server, page, vista, tema, ancho, docente, direccion, clave, monkeypatch
):
    fijar_hora_de_lima(monkeypatch, MIERCOLES_9)
    con_pantalla(page, ancho, tema)
    abrir_vista(page, live_server, vista, docente, direccion, clave)
    if vista == "portada-hoy-pendiente":
        expect(page.locator("#pend-asistencia")).to_have_text("Hoy: pendiente")
    elif vista == "portada-sin-estudiantes":
        expect(page.get_by_text("Tu sección aún no tiene estudiantes")).to_be_visible()
    revisar_con_axe(page, f"{vista}-{tema}-{ancho}")


@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("vista", ["portada", "direccion"])
def test_el_menu_abierto_no_desborda_la_ventana(
    live_server, page, vista, tema, ancho, docente, direccion, clave
):
    con_pantalla(page, ancho, tema)
    abrir_vista(page, live_server, f"{vista}-menu-abierto", docente, direccion, clave)
    page.evaluate("document.fonts.ready")

    ancho_documento = page.evaluate("document.documentElement.scrollWidth")
    panel = page.locator("[data-cuenta-panel]").bounding_box()

    assert ancho_documento <= ancho
    assert panel["x"] >= 0
    assert panel["x"] + panel["width"] <= ancho


@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("vista", ["ingresar", "ingresar-con-error", "ingresar-con-aviso"])
def test_el_inicio_de_sesion_no_desborda(
    live_server, page, vista, tema, ancho, docente, direccion, clave
):
    """«Sin desplazamiento horizontal» con el marco del rebrand (rebrand-us-001, 2.4)."""
    con_pantalla(page, ancho, tema)
    abrir_vista(page, live_server, vista, docente, direccion, clave)
    page.evaluate("document.fonts.ready")

    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    ficha = page.locator(".login-ficha").bounding_box()
    assert ficha["x"] >= 0
    assert ficha["x"] + ficha["width"] <= ancho


@pytest.mark.parametrize("ancho", [320, 360])
def test_b01_un_error_de_campo_sin_espacios_no_desborda(
    live_server, page, ancho, docente, direccion, clave
):
    """Auditoría de Emil, B-01: rb/campo.html es compartido; un error con datos de la docente (80
    caracteres seguidos) se parte dentro de la ficha. En el ingreso los errores son fijos, así que
    el texto se pone a mano sobre el error real de «campos vacíos»."""
    con_pantalla(page, ancho, "light")
    abrir_vista(page, live_server, "ingresar-vacio", docente, direccion, clave)
    page.locator(".field-error span").first.evaluate("(el) => { el.textContent = 'x'.repeat(80); }")
    page.evaluate("document.fonts.ready")

    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    ficha = page.locator(".login-ficha").bounding_box()
    error = page.locator(".field-error").first.bounding_box()
    assert ficha["x"] >= 0
    assert ficha["x"] + ficha["width"] <= ancho
    assert error["x"] + error["width"] <= ficha["x"] + ficha["width"]


@pytest.mark.parametrize("ancho", ANCHOS)
def test_el_ojo_mide_44_px_dentro_del_campo(live_server, page, ancho, docente, direccion, clave):
    con_pantalla(page, ancho, "light")
    abrir_vista(page, live_server, "ingresar", docente, direccion, clave)

    ojo = page.get_by_role("button", name="Mostrar contraseña").bounding_box()
    campo = campo_clave(page).bounding_box()

    assert (ojo["width"], ojo["height"]) == (44, 44)
    assert campo["x"] <= ojo["x"] and ojo["x"] + ojo["width"] <= campo["x"] + campo["width"]
    assert campo["y"] <= ojo["y"] and ojo["y"] + ojo["height"] <= campo["y"] + campo["height"]


@pytest.mark.parametrize(("ancho", "letra"), [(360, "30px"), (1280, "40px")])
def test_el_nombre_de_la_ie_mide_40_px_en_pc_y_30_en_celular(
    live_server, page, ancho, letra, docente, direccion, clave
):
    con_pantalla(page, ancho, "light")
    abrir_vista(page, live_server, "ingresar", docente, direccion, clave)

    nombre = page.get_by_role("heading", level=1)
    assert nombre.evaluate("(el) => getComputedStyle(el).fontSize") == letra


@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("tema", TEMAS)
def test_sin_permiso_no_desborda_y_su_boton_es_tactil(
    live_server, page, tema, ancho, docente, direccion, clave
):
    con_pantalla(page, ancho, tema)
    abrir_vista(page, live_server, "sin-permiso", docente, direccion, clave)
    page.evaluate("document.fonts.ready")

    boton = page.get_by_role("link", name="Volver a tu inicio").bounding_box()
    contenido = page.locator("main .permission").bounding_box()

    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    assert boton["height"] >= 44
    assert boton["x"] >= 0
    assert boton["x"] + boton["width"] <= ancho
    # En celular, el botón principal va a todo el ancho del contenido (boceto).
    assert boton["x"] == pytest.approx(contenido["x"], abs=0.5)
    assert boton["width"] == pytest.approx(contenido["width"], abs=0.5)


@pytest.mark.parametrize("ancho", ANCHOS)
def test_sin_permiso_controles_del_marco_de_44_px(
    live_server, page, ancho, docente, direccion, clave
):
    """El ☰, el ✕ y la cuenta miden 44 × 44 px en su caja real (A-01)."""
    con_pantalla(page, ancho, "light")
    abrir_vista(page, live_server, "sin-permiso", docente, direccion, clave)

    controles = [
        page.get_by_role("button", name="Menú de navegación"),
        page.get_by_label("Menú de la cuenta"),
    ]
    for control in controles:
        caja = control.bounding_box()
        assert (caja["width"], caja["height"]) == (44, 44)

    page.get_by_role("button", name="Menú de navegación").click()
    expect(page.locator("dialog#navegacion")).to_have_js_property("open", True)
    page.wait_for_function("document.getAnimations().length === 0")
    caja = page.get_by_role("button", name="Cerrar navegación").bounding_box()
    assert (caja["width"], caja["height"]) == (44, 44)
