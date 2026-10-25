"""Accesibilidad con axe-core en las pantallas de US-001 y US-002 (spec pantallas-de-inicio; D10).

Ocho vistas (inicio de sesión normal, con error, con campos vacíos y con el aviso de inactividad;
portada y dirección, cada una con el menú cerrado y abierto) en
tema claro y oscuro, a 360 y 1280 px. Falla ante infracciones ``critical`` o ``serious`` de WCAG 2.1
A y AA, el contraste incluido (RNF-008), y guarda el informe en ``test-results/``. axe-core llega
por npm (``npm ci`` en ``src/frontend/``). Se pide con ``uv run pytest -m e2e --browser chromium``.
"""

import json
from pathlib import Path

import pytest

from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    abrir_ingresar,
    boton_ingresar,
    campo_clave,
    campo_usuario,
    con_pantalla,
    envejecer_sesion,
    ingresar,
)

pytestmark = pytest.mark.e2e

RAIZ = Path(__file__).resolve().parents[4]
AXE = RAIZ / "src" / "frontend" / "node_modules" / "axe-core" / "axe.min.js"
INFORMES = RAIZ / "test-results"
ETIQUETAS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
IMPACTOS_QUE_FALLAN = {"critical", "serious"}
VISTAS = [
    "ingresar",
    "ingresar-con-error",
    "ingresar-vacio",
    "ingresar-con-aviso",
    "portada",
    "portada-menu-abierto",
    "direccion",
    "direccion-menu-abierto",
]


def abrir_vista(page, live_server, vista, docente, direccion, clave):
    if vista == "ingresar":
        abrir_ingresar(page, live_server)
    elif vista == "ingresar-con-error":
        abrir_ingresar(page, live_server)
        campo_usuario(page).fill(docente.username)
        campo_clave(page).fill(f"{clave}-incorrecta")
        boton_ingresar(page).click()
        page.get_by_role("alert").wait_for()
    elif vista == "ingresar-vacio":
        abrir_ingresar(page, live_server)
        boton_ingresar(page).click()
        page.locator(".campo__error").first.wait_for()
    elif vista == "ingresar-con-aviso":
        ingresar(page, live_server, docente, clave)
        page.wait_for_url("**/docente/")
        envejecer_sesion(page, 61)
        page.reload()
        page.locator(".mensaje--aviso").wait_for()
        # axe mide el color calculado: a media animación de entrada lo mezcla con la opacidad.
        page.wait_for_function("document.getAnimations().length === 0")
    else:
        es_portada = vista.startswith("portada")
        ingresar(page, live_server, docente if es_portada else direccion, clave)
        page.wait_for_url(f"**/{'docente' if es_portada else 'direccion'}/")
        if vista.endswith("-menu-abierto"):
            page.wait_for_load_state("load")
            page.get_by_label("Menú de la cuenta").click()
            page.locator(".menu-cuenta__panel").wait_for()


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("vista", VISTAS)
def test_sin_infracciones_graves_de_accesibilidad(
    live_server, page, vista, tema, ancho, docente, direccion, clave
):
    con_pantalla(page, ancho, tema)
    abrir_vista(page, live_server, vista, docente, direccion, clave)
    page.evaluate("document.fonts.ready")

    page.add_script_tag(path=str(AXE))
    resultado = page.evaluate(
        "(etiquetas) => axe.run(document, { runOnly: { type: 'tag', values: etiquetas } })",
        ETIQUETAS,
    )

    graves = [v for v in resultado["violations"] if v["impact"] in IMPACTOS_QUE_FALLAN]
    if graves:
        INFORMES.mkdir(exist_ok=True)
        informe = INFORMES / f"accesibilidad-{vista}-{tema}-{ancho}.json"
        informe.write_text(json.dumps(graves, ensure_ascii=False, indent=2), encoding="utf-8")
        resumen = [
            f"{v['id']} ({v['impact']}): {[nodo['target'] for nodo in v['nodes']]}" for v in graves
        ]
        pytest.fail(f"axe: {len(graves)} infracciones, informe en {informe}\n" + "\n".join(resumen))


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
    panel = page.locator(".menu-cuenta__panel").bounding_box()

    assert ancho_documento <= ancho
    assert panel["x"] >= 0
    assert panel["x"] + panel["width"] <= ancho
