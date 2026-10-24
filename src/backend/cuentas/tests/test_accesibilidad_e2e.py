"""Accesibilidad con axe-core en las pantallas de US-001 (spec pantallas-de-inicio; D10).

Cinco vistas (inicio de sesión normal, con error y con campos vacíos, portada y dirección) en
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
    ingresar,
)

pytestmark = pytest.mark.e2e

RAIZ = Path(__file__).resolve().parents[4]
AXE = RAIZ / "src" / "frontend" / "node_modules" / "axe-core" / "axe.min.js"
INFORMES = RAIZ / "test-results"
ETIQUETAS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
IMPACTOS_QUE_FALLAN = {"critical", "serious"}
VISTAS = ["ingresar", "ingresar-con-error", "ingresar-vacio", "portada", "direccion"]


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
    else:
        ingresar(page, live_server, docente if vista == "portada" else direccion, clave)
        page.wait_for_url(f"**/{'docente' if vista == 'portada' else 'direccion'}/")


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
