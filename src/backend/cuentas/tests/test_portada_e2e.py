"""Portada del docente y desborde horizontal en el navegador (spec pantallas-de-inicio; D10).

Chip sin historial (R-19), aviso de "Próximamente" y ``scrollWidth <= clientWidth`` a 320, 360 y
1280 en ambos temas. Desde US-030, la píldora "Hoy: pendiente": aparece una vez, sin movimiento
con "reducir movimiento", y la portada con y sin ella pasa axe. Necesita el CSS compilado y
Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re
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
TARJETAS = ("sesiones", "notas", "asistencia")
DESIGN_MD = Path(__file__).resolve().parents[4] / "DESIGN.md"


def chip_de(page, titulo):
    return page.get_by_role("navigation", name="Accesos").get_by_role("link", name=titulo)


def chip_notas(page):
    return chip_de(page, "Notas")


def esperar_reposo(page):
    """Espera al fin del desplazamiento suave: el carrusel quieto durante 10 cuadros seguidos."""
    page.evaluate(
        """() => new Promise((resolver) => {
            const pista = document.querySelector("[data-carrusel]");
            let ultimo = pista.scrollLeft, quietos = 0;
            const medir = () => {
                quietos = pista.scrollLeft === ultimo ? quietos + 1 : 0;
                ultimo = pista.scrollLeft;
                quietos >= 10 ? resolver() : requestAnimationFrame(medir);
            };
            requestAnimationFrame(medir);
        })"""
    )


def test_chip_notas_muestra_la_tarjeta_sin_tocar_el_historial(live_server, page, docente, clave):
    con_pantalla(page, 360, "light")
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    historial = page.evaluate("history.length")

    chip = chip_notas(page)
    chip.click()

    expect(page.locator("#c-notas")).to_be_in_viewport(ratio=0.9)
    esperar_reposo(page)
    expect(chip).to_have_attribute("aria-current", "true")
    for otro in ("Sesiones", "Asistencia"):
        expect(chip_de(page, otro)).to_have_attribute("aria-current", "false")
    # El punto de Notas es el ancho (24 px) y los otros dos el angosto (8 px). El ancho lo da una
    # animación ligada al desplazamiento: se compara con tolerancia, no con un valor exacto.
    anchos = page.evaluate(
        "[...document.querySelectorAll('.punto')].map((p) => parseFloat(getComputedStyle(p).width))"
    )
    assert anchos[1] >= 23.5, anchos
    assert anchos[0] <= 8.5 and anchos[2] <= 8.5, anchos
    expect(page).to_have_url(f"{live_server.url}/docente/")
    assert page.evaluate("history.length") == historial


def test_tarjeta_proximamente_avisa_sin_mover_la_miniatura(live_server, page, docente, clave):
    con_pantalla(page, 360, "light")
    ingresar(page, live_server, docente, clave)
    chip_notas(page).click()
    expect(page.locator("#c-notas")).to_be_in_viewport(ratio=0.9)
    esperar_reposo(page)
    miniatura = page.locator("#c-notas .franjas")
    antes = miniatura.bounding_box()
    aviso = page.locator("#c-notas .dimension__aviso")
    expect(aviso).to_have_text("")

    # force: Playwright no da por habilitado un botón con aria-disabled, pero recibe el toque.
    page.get_by_role("button", name="Notas", exact=True).click(force=True)

    expect(aviso).to_have_text(AVISO)
    assert miniatura.bounding_box() == antes
    expect(page).to_have_url(f"{live_server.url}/docente/")


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


def valores_oscuros_de_design_md():
    """Los tokens del bloque ``prefers-color-scheme: dark`` del Quick Start de DESIGN.md."""
    quick_start = DESIGN_MD.read_text(encoding="utf-8").split("## Quick Start", 1)[1]
    oscuro = quick_start.split("prefers-color-scheme: dark", 1)[1].split("@media", 1)[0]
    return dict(re.findall(r"(--color-[\w-]+):\s*(#[0-9a-fA-F]{6});", oscuro))


def a_rgb(hexadecimal):
    r, g, b = (int(hexadecimal[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgb({r}, {g}, {b})"


def test_sin_javascript_los_chips_llevan_a_las_tres_tarjetas(live_server, browser, docente, clave):
    contexto = browser.new_context(
        java_script_enabled=False, viewport={"width": 360, "height": 800}
    )
    page = contexto.new_page()
    try:
        ingresar(page, live_server, docente, clave)
        expect(page).to_have_url(f"{live_server.url}/docente/")
        # Sin JavaScript no hay Alpine: el carrusel no toma el control (D7).
        expect(page.locator(".portada")).not_to_have_attribute("data-carrusel-js", re.compile(".*"))

        for clave_tarjeta in TARJETAS:
            titulo = clave_tarjeta.capitalize()
            chip_de(page, titulo).click()

            expect(page).to_have_url(f"{live_server.url}/docente/#c-{clave_tarjeta}")
            expect(page.locator(f"#c-{clave_tarjeta}")).to_be_in_viewport(ratio=0.9)
    finally:
        contexto.close()


def test_a_1280_las_tres_tarjetas_van_en_una_fila_sin_chips_ni_puntos(
    live_server, page, docente, clave
):
    con_pantalla(page, 1280, "light")
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")

    cajas = [page.locator(f"#c-{t}").bounding_box() for t in TARJETAS]

    assert all(caja["width"] > 0 for caja in cajas), cajas
    # En el carrusel del celular también van en una fila, pero la tercera queda fuera de la ventana.
    assert all(caja["x"] + caja["width"] <= 1280 for caja in cajas), cajas
    assert len({round(caja["y"]) for caja in cajas}) == 1, cajas
    izquierdas = [caja["x"] for caja in cajas]
    assert izquierdas == sorted(izquierdas) and len(set(izquierdas)) == 3, cajas
    for caja, siguiente in zip(cajas, cajas[1:], strict=False):
        assert caja["x"] + caja["width"] <= siguiente["x"], cajas
    expect(page.get_by_role("navigation", name="Accesos")).to_be_hidden()
    expect(page.locator(".puntos")).to_be_hidden()
    for punto in page.locator(".punto").all():
        expect(punto).to_be_hidden()


@pytest.mark.parametrize("tema", TEMAS)
def test_los_tokens_aplicados_toman_su_valor_del_tema(live_server, page, docente, clave, tema):
    con_pantalla(page, 1280, tema)
    ingresar(page, live_server, docente, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    oscuros = valores_oscuros_de_design_md()
    claros = {
        "--color-fondo": "#f3eee3",
        "--color-texto": "#2c150c",
        "--color-primario": "#5b2610",
    }

    for token, selector, propiedad in [
        ("--color-fondo", "body", "backgroundColor"),
        ("--color-texto", "body", "color"),
        ("--color-primario", "h1", "color"),
    ]:
        esperado = a_rgb(oscuros[token] if tema == "dark" else claros[token])
        calculado = page.evaluate(
            "([sel, prop]) => getComputedStyle(document.querySelector(sel))[prop]",
            [selector, propiedad],
        )
        assert calculado == esperado, (tema, token, calculado, esperado)


# --- "Hoy: pendiente" en la tarjeta Asistencia (US-030; DESIGN.md 0.4, Movimiento) ---

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


def completar_la_jornada(seccion):
    jornada = Jornada.objects.create(
        seccion=seccion, fecha=MIERCOLES, registrado_por=seccion.docente
    )
    for estudiante in seccion.estudiantes.all():
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")


def pildora(page):
    return page.locator("#pend-asistencia")


def esperar_la_subida(page):
    """La subida termina; con ``both`` la animación sigue en ``getAnimations()``, ya terminada."""
    page.wait_for_function(
        """() => [...document.querySelectorAll(".pildora-pendiente")]
            .flatMap((p) => p.getAnimations())
            .every((a) => a.playState === "finished")"""
    )


def animaciones(page):
    return pildora(page).evaluate(
        "(p) => p.getAnimations().map((a) => [a.animationName, a.effect.getTiming().iterations])"
    )


@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_pildora_aparece_una_vez_con_una_subida_corta(
    live_server, page, seccion_de_ana, docente, clave, ancho
):
    con_pantalla(page, ancho, "light")
    ingresar(page, live_server, docente, clave)

    expect(pildora(page)).to_have_text("Hoy: pendiente")
    assert animaciones(page) == [["subir-pildora", 1]]
    esperar_la_subida(page)
    expect(pildora(page)).to_have_css("opacity", "1")
    expect(pildora(page)).to_be_in_viewport()


def test_con_reducir_movimiento_la_pildora_ya_esta_en_su_lugar(
    live_server, page, seccion_de_ana, docente, clave
):
    con_pantalla(page, 360, "light")
    page.emulate_media(reduced_motion="reduce")
    ingresar(page, live_server, docente, clave)

    expect(pildora(page)).to_have_text("Hoy: pendiente")
    assert animaciones(page) == []
    expect(pildora(page)).to_have_css("opacity", "1")


def test_la_tarjeta_asistencia_lleva_a_la_asistencia_de_hoy(
    live_server, page, seccion_de_ana, docente, clave
):
    con_pantalla(page, 1280, "light")
    ingresar(page, live_server, docente, clave)
    enlace = page.get_by_role("link", name="Asistencia", exact=True)
    expect(enlace).to_have_accessible_description("Registrar asistencia Hoy: pendiente")

    enlace.click()

    expect(page).to_have_url(f"{live_server.url}/docente/secciones/{seccion_de_ana.pk}/asistencia/")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("con_pildora", [True, False], ids=["con-pildora", "completa"])
def test_la_portada_con_y_sin_pildora_pasa_axe(
    live_server, page, seccion_de_ana, docente, clave, ancho, tema, con_pildora
):
    if not con_pildora:
        completar_la_jornada(seccion_de_ana)
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente, clave)
    expect(pildora(page)).to_have_count(1 if con_pildora else 0)
    # axe mide el color calculado: a media subida lo mezcla con la opacidad.
    esperar_la_subida(page)

    nombre = "con-pildora" if con_pildora else "completa"
    revisar_con_axe(page, f"portada-{nombre}-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", [320, 360, 1280])
def test_la_portada_con_la_pildora_no_se_desplaza_en_horizontal(
    live_server, page, seccion_de_ana, docente, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente, clave)
    expect(pildora(page)).to_be_attached()
    page.evaluate("document.fonts.ready")

    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
