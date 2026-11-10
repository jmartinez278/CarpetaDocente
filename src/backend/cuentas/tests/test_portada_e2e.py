"""Portada del docente en el navegador (spec pantallas-de-inicio; rebrand-portada, D4, D5 y D7).

Rejilla a 1280 px y tarjetas apiladas a 360, miniaturas con el papel fijo en los dos temas, tokens
leídos de la hoja del rebrand, aviso de «Próximamente» sin Alpine, «Hoy: pendiente» sin animación y
``scrollWidth <= clientWidth`` a 320, 360 y 1280 en ambos temas. Necesita el CSS compilado y
Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from asistencia.models import Asistencia, Jornada
from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    abrir_ingresar,
    con_pantalla,
    fijar_hora_de_lima,
    ingresar,
    revisar_con_axe,
)
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.e2e

AVISO = "Llegará en una próxima versión."
TARJETAS = ("asistencia", "sesiones", "notas")
TOKENS = Path(__file__).resolve().parents[4] / "src" / "frontend" / "css" / "rebrand" / "tokens.css"
PAPEL = "rgb(250, 246, 239)"  # --preview-paper, igual en los dos temas


def abrir_portada(page, live_server, docente, clave, ancho=1280, tema="light"):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    page.evaluate("document.fonts.ready")


def caja(page, selector):
    return page.locator(selector).bounding_box()


# --- Rejilla (escenarios «Tarjetas en la computadora» y «Tarjetas en el celular»; D4) ---


def test_a_1280_asistencia_ocupa_la_columna_principal(live_server, page, docente, clave):
    abrir_portada(page, live_server, docente, clave, 1280)
    asistencia, sesiones, notas = (caja(page, f"#c-{t}") for t in TARJETAS)

    assert asistencia["x"] + asistencia["width"] < sesiones["x"], (asistencia, sesiones)
    assert asistencia["width"] > sesiones["width"]
    assert sesiones["x"] == pytest.approx(notas["x"], abs=0.5)
    assert sesiones["y"] + sesiones["height"] <= notas["y"]
    # Asistencia cubre las dos filas: arriba con Sesiones y abajo con Notas.
    assert asistencia["y"] == pytest.approx(sesiones["y"], abs=0.5)
    assert asistencia["y"] + asistencia["height"] == pytest.approx(
        notas["y"] + notas["height"], abs=0.5
    )


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


@pytest.mark.parametrize("ancho", ANCHOS)
def test_en_asistencia_el_boton_va_debajo_de_la_miniatura(
    live_server, page, seccion_de_ana, docente, clave, ancho
):
    """Como en el boceto: título y frase, luego el gráfico y al final la acción."""
    abrir_portada(page, live_server, docente, clave, ancho)
    frase = caja(page, "#c-asistencia .dimension-frase")
    miniatura = caja(page, "#c-asistencia .miniatura")
    accion = caja(page, "#c-asistencia .dimension-accion")

    assert miniatura["y"] >= frase["y"] + frase["height"]
    assert accion["y"] >= miniatura["y"] + miniatura["height"]


@pytest.mark.parametrize("tema", TEMAS)
def test_las_miniaturas_llevan_el_mismo_papel_en_los_dos_temas(
    live_server, page, docente, clave, tema
):
    abrir_portada(page, live_server, docente, clave, 1280, tema)

    for t in ("asistencia", "sesiones"):
        fondo = page.locator(f"#c-{t} .miniatura").evaluate(
            "(el) => getComputedStyle(el).backgroundColor"
        )
        assert fondo == PAPEL, (t, tema, fondo)


# --- Tokens (D4): los colores salen de la hoja del rebrand ---


def tokens_del_tema(tema):
    hoja = TOKENS.read_text(encoding="utf-8")
    if tema == "light":
        bloque = hoja.split("@theme static {", 1)[1].split("}", 1)[0]
    else:
        bloque = hoja.split("html[data-theme=dark] {", 1)[1].split("}", 1)[0]
    return dict(re.findall(r"(--[\w-]+):\s*(#[0-9A-Fa-f]{6});", bloque))


def a_rgb(hexadecimal):
    r, g, b = (int(hexadecimal[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgb({r}, {g}, {b})"


@pytest.mark.parametrize("tema", TEMAS)
def test_los_tokens_aplicados_toman_su_valor_del_tema(live_server, page, docente, clave, tema):
    abrir_portada(page, live_server, docente, clave, 1280, tema)
    tokens = tokens_del_tema(tema)

    for token, selector, propiedad in [
        ("--g-main", "body", "backgroundColor"),
        ("--ink", "body", "color"),
        ("--card", "#c-sesiones", "backgroundColor"),
        ("--cocoa", "#c-asistencia", "backgroundColor"),
    ]:
        calculado = page.locator(selector).evaluate(f"(el) => getComputedStyle(el).{propiedad}")
        assert calculado == a_rgb(tokens[token]), (tema, token, calculado)


@pytest.mark.parametrize("ancho", ANCHOS)
def test_el_saludo_hereda_la_altura_de_linea_del_titulo(live_server, page, docente, clave, ancho):
    """Como en el boceto, «Buenos días,» no lleva su propia altura de línea: con 1,4 el bloque
    bajaba unos 6 px y empujaba la portada."""
    abrir_portada(page, live_server, docente, clave, ancho)

    proporciones = page.evaluate(
        """() => ["h1", "h1 .saludo"].map((s) => {
            const e = getComputedStyle(document.querySelector(s));
            return Math.round((parseFloat(e.lineHeight) / parseFloat(e.fontSize)) * 100) / 100;
        })"""
    )

    assert proporciones[0] == proporciones[1], proporciones


@pytest.mark.parametrize("tema", TEMAS)
def test_la_barra_de_la_portada_no_es_una_franja_ni_se_queda_fija(
    live_server, page, docente, clave, tema
):
    """Como en el boceto: solo flota el botón de la cuenta, sin fondo, sin línea y sin fijar."""
    abrir_portada(page, live_server, docente, clave, 360, tema)

    barra = page.locator("header.appbar")
    estilo = barra.evaluate(
        """(el) => {
            const e = getComputedStyle(el);
            return { posicion: e.position, fondo: e.backgroundColor, borde: e.borderBottomWidth };
        }"""
    )
    assert estilo == {"posicion": "static", "fondo": "rgba(0, 0, 0, 0)", "borde": "0px"}
    page.mouse.wheel(0, 400)
    page.wait_for_timeout(200)
    assert barra.bounding_box()["y"] < 0 or page.evaluate("window.scrollY") == 0


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


def test_tarjeta_proximamente_avisa_sin_mover_la_miniatura(live_server, page, docente, clave):
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


def test_un_segundo_toque_vuelve_a_escribir_el_aviso(live_server, page, docente, clave):
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


def test_el_aviso_se_vacia_a_los_tres_segundos(live_server, page, docente, clave):
    abrir_portada(page, live_server, docente, clave, 1280)
    page.wait_for_load_state("load")
    aviso = page.locator("#c-sesiones .dimension-aviso")

    page.get_by_role("button", name="Sesiones", exact=True).click(force=True)
    expect(aviso).to_have_text(AVISO)
    escrito = time.monotonic()

    expect(aviso).to_have_text("", timeout=5000)
    assert time.monotonic() - escrito >= 2.5


# --- Ancho (requisito «Sin desplazamiento horizontal») ---


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", [320, 360, 1280])
@pytest.mark.parametrize("pantalla", ["ingresar", "docente", "direccion"])
def test_el_documento_no_se_desplaza_en_horizontal(
    live_server, page, request, pantalla, ancho, tema, clave
):
    con_pantalla(page, ancho, tema)
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


@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_pildora_no_tiene_animacion(live_server, page, seccion_de_ana, docente, clave, ancho):
    """D7: «Hoy: pendiente» está en su lugar desde el inicio, sin subida de entrada."""
    abrir_portada(page, live_server, docente, clave, ancho)

    expect(pildora(page)).to_have_text("Hoy: pendiente")
    assert pildora(page).evaluate("(p) => getComputedStyle(p).animationName") == "none"
    assert pildora(page).evaluate("(p) => p.getAnimations().length") == 0
    expect(pildora(page)).to_have_css("opacity", "1")
    expect(pildora(page)).to_be_in_viewport()


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
@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("con_pildora", [True, False], ids=["con-pildora", "completa"])
def test_la_portada_con_y_sin_pildora_pasa_axe(
    live_server, page, seccion_de_ana, docente, clave, ancho, tema, con_pildora
):
    if not con_pildora:
        completar_la_jornada(seccion_de_ana)
    abrir_portada(page, live_server, docente, clave, ancho, tema)
    expect(pildora(page)).to_have_count(1 if con_pildora else 0)

    nombre = "con-pildora" if con_pildora else "completa"
    revisar_con_axe(page, f"portada-{nombre}-{ancho}-{tema}")


def sin_desplazamiento(page):
    return page.evaluate(
        """() => [document.documentElement, document.querySelector(".accesos")]
            .map((el) => ({ancho: el.scrollWidth, visible: el.clientWidth}))"""
    )


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", [320, 360])
@pytest.mark.parametrize("caso", ["pildora", "sin-estudiantes"])
def test_la_portada_no_se_desplaza_en_horizontal(
    live_server, page, request, docente, clave, ancho, tema, caso
):
    """Escenario «Portada sin desplazamiento interno»."""
    request.getfixturevalue("seccion_de_ana" if caso == "pildora" else "seccion_vacia")
    abrir_portada(page, live_server, docente, clave, ancho, tema)
    if caso == "pildora":
        expect(pildora(page)).to_be_visible()
    else:
        expect(page.get_by_text("Tu sección aún no tiene estudiantes")).to_be_visible()

    for medida in sin_desplazamiento(page):
        assert medida["ancho"] <= medida["visible"], (caso, medida)
