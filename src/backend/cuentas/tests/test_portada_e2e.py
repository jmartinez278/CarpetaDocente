"""Portada del docente en el navegador (spec pantallas-de-inicio; rebrand-portada, D4, D5 y D7).

Tarjetas apiladas a 360, aviso de «Próximamente» sin Alpine, ``scrollWidth <= clientWidth`` a 320,
360 y 1280 y axe a 360 en ambos temas. Necesita el CSS
compilado y Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from asistencia.models import Asistencia, Jornada
from cuentas.tests.e2e import (
    TEMAS,
    abrir_ingresar,
    con_pantalla,
    fijar_hora_de_lima,
    ingresar,
    revisar_con_axe,
    sesiones_proximamente,
)
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.e2e

AVISO = "Llegará en una próxima versión."
TARJETAS = ("asistencia", "sesiones", "notas")


def abrir_portada(page, live_server, docente, clave, ancho=1280, tema="light"):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    page.evaluate("document.fonts.ready")


def caja(page, selector):
    return page.locator(selector).bounding_box()


# --- Rejilla (escenarios «Tarjetas en la computadora» y «Tarjetas en el celular»; D4) ---


def test_a_360_las_tres_se_apilan_en_el_orden_del_dom(live_server, page, docente, clave):
    abrir_portada(page, live_server, docente, clave, 360)
    cajas = [caja(page, f"#c-{t}") for t in TARJETAS]

    assert len({round(c["x"]) for c in cajas}) == 1, cajas
    for arriba, abajo in zip(cajas, cajas[1:], strict=False):
        assert arriba["y"] + arriba["height"] <= abajo["y"], cajas
    for c in cajas:
        assert c["x"] >= 0 and c["x"] + c["width"] <= 360, c


@pytest.mark.parametrize("clave_tarjeta", ["sesiones", "notas"])
def test_a_360_sesiones_y_notas_llevan_la_miniatura_junto_al_texto(
    live_server, page, docente, clave, clave_tarjeta
):
    abrir_portada(page, live_server, docente, clave, 360)
    texto = caja(page, f"#c-{clave_tarjeta} .dimension-copia")
    miniatura = caja(page, f"#c-{clave_tarjeta} .miniatura")

    assert miniatura["x"] >= texto["x"] + texto["width"], (texto, miniatura)
    assert miniatura["y"] < texto["y"] + texto["height"], (texto, miniatura)


# --- Tokens (D4): los colores salen de la hoja del rebrand ---


# --- «Próximamente» sin Alpine (D5) ---


def grabar_aviso(page, selector):
    """Guarda cada texto que toma la región del aviso, en orden."""
    page.locator(selector).evaluate(
        """(el) => {
            window.textosDelAviso = [];
            new MutationObserver(() => window.textosDelAviso.push(el.textContent))
                .observe(el, { childList: true, characterData: true, subtree: true });
        }"""
    )


def test_tarjeta_proximamente_avisa_sin_mover_la_miniatura(
    live_server, page, docente, clave, monkeypatch
):
    sesiones_proximamente(monkeypatch)
    abrir_portada(page, live_server, docente, clave, 360)
    page.wait_for_load_state("load")
    miniatura = page.locator("#c-sesiones .miniatura")
    antes = miniatura.bounding_box()
    aviso = page.locator("#c-sesiones .dimension-aviso")
    expect(aviso).to_have_text("")
    expect(aviso).to_have_attribute("aria-live", "polite")

    # force: Playwright no da por habilitado un botón con aria-disabled, pero recibe el toque.
    page.get_by_role("button", name="Sesiones", exact=True).click(force=True)

    expect(aviso).to_have_text(AVISO)
    assert miniatura.bounding_box() == antes
    expect(page).to_have_url(f"{live_server.url}/docente/")


def test_un_segundo_toque_vuelve_a_escribir_el_aviso(
    live_server, page, docente, clave, monkeypatch
):
    sesiones_proximamente(monkeypatch)
    abrir_portada(page, live_server, docente, clave, 360)
    page.wait_for_load_state("load")
    boton = page.get_by_role("button", name="Sesiones", exact=True)
    aviso = page.locator("#c-sesiones .dimension-aviso")
    boton.click(force=True)
    expect(aviso).to_have_text(AVISO)
    grabar_aviso(page, "#c-sesiones .dimension-aviso")

    boton.click(force=True)

    expect(aviso).to_have_text(AVISO)
    # Se vacía y se vuelve a escribir: el lector lo anuncia otra vez.
    assert page.evaluate("window.textosDelAviso") == ["", AVISO]


def test_el_aviso_se_vacia_a_los_tres_segundos(live_server, page, docente, clave, monkeypatch):
    sesiones_proximamente(monkeypatch)
    abrir_portada(page, live_server, docente, clave, 1280)
    page.wait_for_load_state("load")
    aviso = page.locator("#c-sesiones .dimension-aviso")

    page.get_by_role("button", name="Sesiones", exact=True).click(force=True)
    expect(aviso).to_have_text(AVISO)
    escrito = time.monotonic()

    expect(aviso).to_have_text("", timeout=5000)
    assert time.monotonic() - escrito >= 2.5


# --- Ancho (requisito «Sin desplazamiento horizontal») ---


@pytest.mark.parametrize("ancho", [320, 360, 1280])
@pytest.mark.parametrize("pantalla", ["ingresar", "docente"])
def test_el_documento_no_se_desplaza_en_horizontal(
    live_server, page, request, pantalla, ancho, clave
):
    con_pantalla(page, ancho, "light")
    if pantalla == "ingresar":
        abrir_ingresar(page, live_server)
    else:
        ingresar(page, live_server, request.getfixturevalue(pantalla), clave)
        expect(page).to_have_url(f"{live_server.url}/{pantalla}/")

    medidas = page.evaluate(
        "({ancho: document.documentElement.scrollWidth,"
        " ventana: document.documentElement.clientWidth})"
    )
    assert medidas["ancho"] <= medidas["ventana"], medidas


# --- "Hoy: pendiente" y la sección sin estudiantes (US-030, US-006) ---

MIERCOLES = date(2026, 10, 28)


@pytest.fixture
def seccion_de_ana(docente, monkeypatch):
    """Un miércoles a las 9:00 de Lima, con "2.º grado, sección A" de Ana y tres estudiantes."""
    fijar_hora_de_lima(monkeypatch, datetime(2026, 10, 28, 9, 0, tzinfo=ZoneInfo("America/Lima")))
    anio = AnioEscolar.objects.create(institucion=docente.institucion, anio=2027)
    seccion = Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)
    for apellidos in ("AGUILAR FLORES", "BRAVO CASAS", "CRUZ HUAMÁN"):
        Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres="ANA")
    return seccion


@pytest.fixture
def seccion_vacia(docente):
    anio = AnioEscolar.objects.create(institucion=docente.institucion, anio=2027)
    return Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)


def completar_la_jornada(seccion):
    jornada = Jornada.objects.create(
        seccion=seccion, fecha=MIERCOLES, registrado_por=seccion.docente
    )
    for estudiante in seccion.estudiantes.all():
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")


def pildora(page):
    return page.locator("#pend-asistencia")


def test_la_tarjeta_asistencia_lleva_a_la_asistencia_de_hoy(
    live_server, page, seccion_de_ana, docente, clave
):
    abrir_portada(page, live_server, docente, clave, 1280)
    enlace = page.get_by_role("link", name="Asistencia", exact=True)
    expect(enlace).to_have_accessible_description("Registrar asistencia Hoy: pendiente")

    enlace.click()

    expect(page).to_have_url(f"{live_server.url}/docente/secciones/{seccion_de_ana.pk}/asistencia/")


def test_toda_la_tarjeta_notas_lleva_a_la_hoja(live_server, page, seccion_de_ana, docente, clave):
    """El enlace del título se estira sobre la tarjeta: tocar la miniatura también lleva (D4)."""
    abrir_portada(page, live_server, docente, clave, 360)
    expect(page.get_by_role("link", name="Notas", exact=True)).to_have_accessible_description(
        "Registrar notas"
    )

    # El enlace estirado cubre la miniatura: el toque en su centro llega al enlace.
    page.locator("#c-notas").scroll_into_view_if_needed()
    miniatura = caja(page, "#c-notas .miniatura")
    page.mouse.click(
        miniatura["x"] + miniatura["width"] / 2, miniatura["y"] + miniatura["height"] / 2
    )

    expect(page).to_have_url(re.compile(rf"/docente/secciones/{seccion_de_ana.pk}/"))


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("con_pildora", [True, False], ids=["con-pildora", "completa"])
def test_la_portada_con_y_sin_pildora_pasa_axe(
    live_server, page, seccion_de_ana, docente, clave, tema, con_pildora
):
    if not con_pildora:
        completar_la_jornada(seccion_de_ana)
    abrir_portada(page, live_server, docente, clave, 360, tema)
    expect(pildora(page)).to_have_count(1 if con_pildora else 0)

    nombre = "con-pildora" if con_pildora else "completa"
    revisar_con_axe(page, f"portada-{nombre}-{tema}")


def sin_desplazamiento(page):
    return page.evaluate(
        """() => [document.documentElement, document.querySelector(".accesos")]
            .map((el) => ({ancho: el.scrollWidth, visible: el.clientWidth}))"""
    )


@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("caso", ["pildora", "sin-estudiantes"])
def test_la_portada_no_se_desplaza_en_horizontal(
    live_server, page, request, docente, clave, ancho, caso
):
    """Escenario «Portada sin desplazamiento interno»."""
    request.getfixturevalue("seccion_de_ana" if caso == "pildora" else "seccion_vacia")
    abrir_portada(page, live_server, docente, clave, ancho)
    if caso == "pildora":
        expect(pildora(page)).to_be_visible()
    else:
        expect(page.get_by_text("Tu sección aún no tiene estudiantes")).to_be_visible()

    for medida in sin_desplazamiento(page):
        assert medida["ancho"] <= medida["visible"], (caso, medida)
