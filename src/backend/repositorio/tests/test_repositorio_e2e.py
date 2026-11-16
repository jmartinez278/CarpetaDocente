"""«Mis sesiones» y «Repositorio» en el navegador, a 360 px (specs repositorio-sesiones y
envio-sesiones; design de US-011, D10 y D12).

Las nueve pruebas del cambio son seis aquí (buscar y filtrar, pestañas, foco y anuncio, panel
«Filtrar», actualización tras enviar, desplazamiento y axe) y tres en ``test_detalle_e2e.py``.
Todo lo demás (permisos, textos, enlaces) es de las pruebas de vista y de plantilla. Necesita el
CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium src/backend/repositorio``.
"""

import re

import pytest
from playwright.sync_api import expect

from catalogo.models import Area
from cuentas.tests.e2e import TEMAS, con_pantalla, ingresar, revisar_con_axe
from repositorio.tests.test_sesiones_e2e import (
    OBJETIVOS_PEQUENOS,
    abrir,
    boton_subir,
    enviar,
    esperar_exito,
    llenar,
    quieto,
)

pytestmark = pytest.mark.e2e

URL = "/docente/sesiones/"
URL_REPOSITORIO = "/docente/sesiones/repositorio/"
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
    """Ingresa a 360 px y abre la dirección pedida."""
    con_pantalla(page, ANCHO, "light")
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")

    def abrir_url(direccion):
        page.goto(f"{live_server.url}{direccion}")
        return page

    return abrir_url


@pytest.fixture
def sesiones_de_colegas(crear_sesion, otra_docente):
    """Cinco compartidas de una colega, en varios grados y áreas."""
    matematica = Area.objects.get(codigo_siagie="063")
    return [
        crear_sesion(
            otra_docente,
            titulo="Escribimos recomendaciones para cuidar el agua",
            grado=3,
            compartida=True,
            texto="Evaluación con lista de cotejo",
        ),
        crear_sesion(
            otra_docente, titulo="Leemos un cuento", grado=3, compartida=True, texto="Cuento"
        ),
        crear_sesion(
            otra_docente,
            titulo="Comparamos fracciones",
            grado=2,
            area=matematica,
            compartida=True,
            texto="Fracciones con el mismo denominador",
        ),
        crear_sesion(otra_docente, titulo="Sumamos", grado=2, area=matematica, compartida=True),
        crear_sesion(otra_docente, titulo="Sin compartir", compartida=False),
    ]


def tarjetas(page):
    return page.locator(".sesion-tarjeta")


def titulo_de_resultados(page):
    return page.locator("#resultados-titulo")


def tab(page, nombre):
    return page.get_by_role("tab", name=re.compile(rf"^{nombre}"))


def boton_filtrar(page):
    return page.get_by_role("button", name=re.compile(r"^Filtrar"))


def panel_de_filtros(page):
    return page.get_by_role("dialog", name="Filtros")


def en_calma(page):
    """HTMX terminó de pedir, cambiar y asentar: una tecla antes de eso llega a la nav vieja."""
    page.wait_for_function(
        "!document.querySelector('.htmx-request, .htmx-swapping, .htmx-settling, .htmx-added')"
    )


def sin_desplazamiento(page):
    return page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )


# --- (1) Buscar, filtrar, «Sin coincidencias», «Borrar filtros» y abrir una sesión ---


def test_buscar_filtrar_ver_sin_coincidencias_borrar_y_abrir_una_sesion(
    entrar, sesiones_de_colegas
):
    page = entrar(URL_REPOSITORIO)
    expect(tarjetas(page)).to_have_count(4)
    expect(titulo_de_resultados(page)).to_have_text("4 sesiones compartidas")

    # Una palabra que solo está en el texto transcrito del archivo.
    page.get_by_role("searchbox", name="Buscar sesiones por título, propósito o texto").fill(
        "COTEJO"
    )
    expect(tarjetas(page)).to_have_count(1)
    expect(titulo_de_resultados(page)).to_have_text("1 sesión")
    expect(page).to_have_url(re.compile(r"\?q=COTEJO$"))

    # Grado y área desde el panel del celular; la búsqueda se conserva.
    page.get_by_role("searchbox").fill("")
    expect(tarjetas(page)).to_have_count(4)
    boton_filtrar(page).click()
    expect(panel_de_filtros(page)).to_be_visible()
    panel_de_filtros(page).get_by_role("link", name="3.º", exact=True).click()
    expect(tarjetas(page)).to_have_count(2)
    panel_de_filtros(page).get_by_role("link", name=re.compile("^Comunicación")).click()
    expect(tarjetas(page)).to_have_count(2)
    expect(page).to_have_url(re.compile(r"grado=3&area=\d+$"))
    panel_de_filtros(page).get_by_role("button", name="Cerrar filtros").click()
    expect(boton_filtrar(page)).to_contain_text("2")

    # Sin coincidencias y «Borrar filtros».
    page.get_by_role("searchbox").fill("zzz")
    expect(page.get_by_text("No se encontraron sesiones con esos filtros")).to_be_visible()
    expect(tarjetas(page)).to_have_count(0)
    page.get_by_role("link", name="Borrar filtros").click()
    expect(tarjetas(page)).to_have_count(4)
    expect(page.get_by_role("searchbox")).to_have_value("")
    expect(boton_filtrar(page)).not_to_contain_text("2")
    expect(page).to_have_url(f"{page.url.split('/docente')[0]}{URL_REPOSITORIO}")

    page.get_by_role("link", name=re.compile("Leemos un cuento")).click()
    expect(page.get_by_role("heading", level=1, name="Leemos un cuento")).to_be_visible()


# --- (2) Pestañas con las flechas, foco y «atrás» ---


def test_las_pestanas_se_manejan_con_las_flechas_y_atras_vuelve(entrar, sesiones_de_colegas):
    page = entrar(URL)
    expect(tab(page, "Mis sesiones")).to_have_attribute("aria-selected", "true")
    expect(tab(page, "Repositorio")).to_contain_text("4")

    tab(page, "Mis sesiones").focus()
    page.keyboard.press("ArrowRight")

    expect(tab(page, "Repositorio")).to_have_attribute("aria-selected", "true")
    expect(tab(page, "Repositorio")).to_be_focused()
    expect(page).to_have_url(re.compile(rf"{URL_REPOSITORIO}$"))
    expect(tarjetas(page)).to_have_count(4)
    en_calma(page)

    page.keyboard.press("ArrowLeft")
    expect(tab(page, "Mis sesiones")).to_have_attribute("aria-selected", "true")
    expect(tab(page, "Mis sesiones")).to_be_focused()
    expect(page).to_have_url(re.compile(rf"{URL}$"))
    en_calma(page)

    page.keyboard.press("ArrowRight")
    expect(tab(page, "Repositorio")).to_have_attribute("aria-selected", "true")
    page.go_back()
    expect(page).to_have_url(re.compile(rf"{URL}$"))
    expect(tab(page, "Mis sesiones")).to_have_attribute("aria-selected", "true")


# --- (3) El buscador conserva el foco y lo escrito, y el total se anuncia ---


def test_el_buscador_conserva_el_foco_y_lo_escrito_mientras_la_lista_cambia(
    entrar, sesiones_de_colegas
):
    page = entrar(URL_REPOSITORIO)
    campo = page.get_by_role("searchbox")

    campo.click()
    campo.press_sequentially("fracc", delay=80)

    expect(tarjetas(page)).to_have_count(1)
    expect(campo).to_be_focused()
    expect(campo).to_have_value("fracc")
    expect(page.locator("#anuncio")).to_have_text("1 sesión")

    campo.press_sequentially("x", delay=80)
    expect(tarjetas(page)).to_have_count(0)
    expect(campo).to_be_focused()
    expect(campo).to_have_value("fraccx")

    page.get_by_role("button", name="Borrar búsqueda").click()
    expect(campo).to_be_focused()
    expect(campo).to_have_value("")
    expect(tarjetas(page)).to_have_count(4)
    expect(page.locator("#anuncio")).to_have_text("4 sesiones compartidas")


# --- (4) El panel «Filtrar» a 360 px ---


def test_el_panel_filtrar_abre_con_foco_aplica_al_tocar_y_esc_lo_cierra(
    entrar, sesiones_de_colegas
):
    page = entrar(URL_REPOSITORIO)
    expect(panel_de_filtros(page)).to_be_hidden()

    boton_filtrar(page).click()

    expect(panel_de_filtros(page)).to_be_visible()
    expect(page.locator("#filtros-titulo")).to_be_focused()
    panel_de_filtros(page).get_by_role("link", name="2.º", exact=True).click()
    expect(tarjetas(page)).to_have_count(2)
    expect(panel_de_filtros(page)).to_be_visible()

    page.keyboard.press("Escape")

    expect(panel_de_filtros(page)).to_be_hidden()
    expect(boton_filtrar(page)).to_be_focused()
    expect(boton_filtrar(page)).to_contain_text("1")

    boton_filtrar(page).click()
    panel_de_filtros(page).get_by_role("button", name="Cerrar filtros").click()
    expect(panel_de_filtros(page)).to_be_hidden()
    expect(boton_filtrar(page)).to_be_focused()


# --- (5) Tras enviar una sesión, la lista y el contador se actualizan ---


def test_tras_enviar_una_sesion_la_lista_y_el_contador_se_actualizan(entrar):
    page = entrar(URL)
    expect(page.get_by_text("Aquí verás las sesiones que envíes y su estado.")).to_be_visible()
    expect(tab(page, "Mis sesiones")).to_contain_text("0")

    abrir(page)
    llenar(page)
    enviar(page).click()
    esperar_exito(page)

    tarjeta = page.get_by_role("link", name=re.compile("Abrir Leemos un cuento"))
    expect(tarjeta).to_be_visible()
    expect(page.get_by_role("heading", name="Hoy")).to_be_visible()
    expect(tab(page, "Mis sesiones")).to_contain_text("1")
    expect(tarjeta).to_contain_text("Enviada")
    expect(page.get_by_text("Aquí verás las sesiones que envíes y su estado.")).to_be_hidden()
    # El botón de la cabecera sigue oculto y «Subir otra» abre otro formulario.
    expect(boton_subir(page)).to_be_hidden()
    page.get_by_role("button", name="Subir otra").click()
    quieto(page)


# --- (6) Sin desplazamiento horizontal y axe, en claro y oscuro ---


def objetivos_pequenos(page):
    return page.evaluate(OBJETIVOS_PEQUENOS)


@pytest.mark.parametrize("tema", TEMAS)
def test_las_listas_y_el_panel_son_accesibles_y_no_se_desplazan(
    live_server, page, docente_con_seccion, clave, crear_sesion, otra_docente, tema
):
    titulo_largo = "L" * 200
    crear_sesion(otra_docente, titulo=titulo_largo, compartida=True, texto="Línea " * 40)
    crear_sesion(docente_con_seccion, titulo="Mi sesión", compartida=True, texto="")
    crear_sesion(docente_con_seccion, titulo="Otra mía", texto="Texto")
    con_pantalla(page, ANCHO, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")

    page.goto(f"{live_server.url}{URL}")
    expect(tarjetas(page)).to_have_count(2)
    revisar_con_axe(page, f"mis-sesiones-{tema}")
    assert sin_desplazamiento(page)
    assert objetivos_pequenos(page) == []

    page.goto(f"{live_server.url}{URL_REPOSITORIO}")
    expect(tarjetas(page)).to_have_count(2)
    tarjeta_larga = page.get_by_role("link", name=re.compile("^Abrir L{200}"))
    expect(tarjeta_larga).to_be_visible()
    assert tarjeta_larga.evaluate("(el) => el.scrollWidth <= el.clientWidth")
    revisar_con_axe(page, f"repositorio-{tema}")
    assert sin_desplazamiento(page)
    assert objetivos_pequenos(page) == []

    boton_filtrar(page).click()
    expect(panel_de_filtros(page)).to_be_visible()
    quieto(page)
    revisar_con_axe(page, f"repositorio-filtros-{tema}")
    assert sin_desplazamiento(page)
    assert objetivos_pequenos(page) == []
