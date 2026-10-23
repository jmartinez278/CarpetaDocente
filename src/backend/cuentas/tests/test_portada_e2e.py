"""Portada del docente y desborde horizontal en el navegador (spec pantallas-de-inicio; D10).

Chip sin historial (R-19), aviso de "Próximamente" y ``scrollWidth <= clientWidth`` a 320, 360 y
1280 en ambos temas. Necesita el CSS compilado y Chromium:
``uv run pytest -m e2e --browser chromium``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import TEMAS, abrir_ingresar, con_pantalla, ingresar

pytestmark = pytest.mark.e2e

AVISO = "Llegará en una próxima versión."


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
