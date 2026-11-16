"""La página de una sesión propia en el navegador, a 360 px (spec detalle-sesion; design de
US-011, D8 y D12).

Eliminar con su diálogo, compartir con los términos y dejar de compartir, y el desplazamiento y
axe de la página y sus dos diálogos. Los permisos, los textos y los enlaces son de las pruebas de
vista y de plantilla. Necesita el CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium src/backend/repositorio``.
"""

import re

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import TEMAS, con_pantalla, ingresar, revisar_con_axe
from repositorio.models import Sesion
from repositorio.tests.test_repositorio_e2e import sin_desplazamiento
from repositorio.tests.test_sesiones_e2e import OBJETIVOS_PEQUENOS, quieto

pytestmark = pytest.mark.e2e

URL = "/docente/sesiones/"
ANCHO = 360


@pytest.fixture(autouse=True)
def _catalogo(catalogo):
    """Las áreas de la institución salen del catálogo, que las e2e vacían al terminar."""


@pytest.fixture
def docente_con_seccion(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return docente


@pytest.fixture
def entrar(live_server, page, docente_con_seccion, clave):
    """Ingresa a 360 px y abre la página de la sesión pedida."""
    con_pantalla(page, ANCHO, "light")
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")

    def abrir_pagina(sesion):
        page.goto(f"{live_server.url}{URL}{sesion.pk}/")
        expect(page.get_by_role("heading", level=1, name=sesion.titulo)).to_be_visible()
        return page

    return abrir_pagina


def dialogo_eliminar(page):
    return page.get_by_role("dialog", name="¿Eliminar esta sesión?")


def dialogo_terminos(page):
    return page.get_by_role("dialog", name="Antes de compartir")


def boton(page, nombre):
    return page.get_by_role("button", name=nombre, exact=True)


# --- (7) Eliminar: diálogo, cancelar y confirmar ---


def test_eliminar_abre_el_dialogo_con_foco_en_cancelar_y_confirmar_lleva_a_mis_sesiones(
    entrar, con_archivo, docente_con_seccion
):
    sesion = con_archivo(docente_con_seccion, titulo="Leemos un cuento", compartida=True)
    page = entrar(sesion)

    boton(page, "Eliminar").click()
    expect(dialogo_eliminar(page)).to_be_visible()
    expect(dialogo_eliminar(page)).to_contain_text("También se retira de la dirección.")
    expect(dialogo_eliminar(page)).to_contain_text(
        "Se eliminarán la sesión y su archivo para todos."
    )
    quieto(page)
    expect(boton(page, "Cancelar")).to_be_focused()

    boton(page, "Cancelar").click()
    expect(dialogo_eliminar(page)).to_be_hidden()
    expect(boton(page, "Eliminar")).to_be_focused()
    assert Sesion.objects.count() == 1

    boton(page, "Eliminar").click()
    quieto(page)
    page.keyboard.press("Escape")
    expect(dialogo_eliminar(page)).to_be_hidden()
    expect(boton(page, "Eliminar")).to_be_focused()

    boton(page, "Eliminar").click()
    quieto(page)
    boton(page, "Eliminar sesión").click()

    expect(page).to_have_url(re.compile(rf"{URL}$"))
    expect(page.get_by_role("status").filter(has_text="Sesión eliminada")).to_be_visible()
    expect(page.get_by_text("Aquí verás las sesiones que envíes y su estado.")).to_be_visible()
    assert Sesion.objects.count() == 0
    page.reload()
    expect(page.get_by_text("Sesión eliminada")).to_have_count(0)


# --- (8) Compartir con los términos y dejar de compartir ---


def test_compartir_abre_los_terminos_volver_devuelve_el_foco_y_aceptar_deja_el_chip(
    entrar, crear_sesion, docente_con_seccion
):
    sesion = crear_sesion(docente_con_seccion, titulo="Leemos un cuento")
    page = entrar(sesion)
    expect(page.get_by_text("Compartida", exact=True)).to_have_count(0)

    boton(page, "Compartir").click()
    expect(dialogo_terminos(page)).to_be_visible()
    quieto(page)
    expect(page.locator("#terminos-compartir-titulo")).to_be_focused()
    expect(dialogo_terminos(page)).to_contain_text("Soy autor(a) de la sesión")

    page.get_by_role("button", name="Volver").click()
    expect(dialogo_terminos(page)).to_be_hidden()
    expect(boton(page, "Compartir")).to_be_focused()
    sesion.refresh_from_db()
    assert sesion.compartida is False

    boton(page, "Compartir").click()
    quieto(page)
    boton(page, "Acepto y comparto").click()

    expect(
        page.get_by_role("status").filter(has_text="Sesión compartida en el repositorio")
    ).to_be_visible()
    expect(page.get_by_text("Compartida", exact=True)).to_be_visible()
    sesion.refresh_from_db()
    assert sesion.compartida is True and sesion.terminos_aceptados_en is not None

    boton(page, "Dejar de compartir").click()

    expect(
        page.get_by_role("status").filter(has_text="Dejaste de compartir la sesión")
    ).to_be_visible()
    expect(page.get_by_text("Compartida", exact=True)).to_have_count(0)
    expect(boton(page, "Compartir")).to_be_visible()
    sesion.refresh_from_db()
    assert sesion.compartida is False


# --- (9) Sin desplazamiento horizontal y axe, en claro y oscuro ---


@pytest.mark.parametrize("tema", TEMAS)
def test_la_pagina_y_sus_dialogos_son_accesibles_y_no_se_desplazan(
    live_server, page, docente_con_seccion, clave, crear_sesion, tema
):
    sesion = crear_sesion(
        docente_con_seccion,
        titulo="T" * 200,
        proposito="Propósito de la sesión",
        texto="Primera línea\n" + "x" * 300,
        compartida=False,
    )
    con_pantalla(page, ANCHO, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    page.goto(f"{live_server.url}{URL}{sesion.pk}/")
    expect(page.get_by_role("heading", level=1)).to_be_visible()

    revisar_con_axe(page, f"sesion-{tema}")
    assert sin_desplazamiento(page)
    assert page.evaluate(OBJETIVOS_PEQUENOS) == []
    assert page.locator(".sesion-texto").evaluate("(el) => el.scrollWidth <= el.clientWidth")

    boton(page, "Eliminar").click()
    expect(dialogo_eliminar(page)).to_be_visible()
    quieto(page)
    revisar_con_axe(page, f"sesion-eliminar-{tema}")
    assert sin_desplazamiento(page)
    assert page.evaluate(OBJETIVOS_PEQUENOS) == []
    boton(page, "Cancelar").click()

    boton(page, "Compartir").click()
    expect(dialogo_terminos(page)).to_be_visible()
    quieto(page)
    revisar_con_axe(page, f"sesion-terminos-{tema}")
    assert sin_desplazamiento(page)
    assert page.evaluate(OBJETIVOS_PEQUENOS) == []
