"""Ayudas comunes de las pruebas de punta a punta de US-001 (no es un módulo de pruebas).

Los usuarios son los ficticios de ``conftest.py`` (``docente``, ``direccion``) y la contraseña es la
de la fixture ``clave``, generada en cada prueba (DoD 8).
"""

import json
from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone

TEMAS = ("light", "dark")
ANCHOS = (360, 1280)
ALTO = 800

RAIZ = Path(__file__).resolve().parents[4]
AXE = RAIZ / "src" / "frontend" / "node_modules" / "axe-core" / "axe.min.js"
INFORMES = RAIZ / "test-results"
ETIQUETAS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
IMPACTOS_QUE_FALLAN = {"critical", "serious"}


def abrir_ingresar(page, live_server):
    page.goto(f"{live_server.url}/ingresar/")


def campo_usuario(page):
    return page.get_by_label("Usuario")


def campo_clave(page):
    # exact: el botón "Mostrar contraseña" también contiene la palabra.
    return page.get_by_label("Contraseña", exact=True)


def boton_ingresar(page):
    return page.get_by_role("button", name="Ingresar", exact=True)


def ingresar(page, live_server, usuario, clave):
    """Recorre el inicio de sesión como lo haría la persona, hasta enviar el formulario."""
    abrir_ingresar(page, live_server)
    campo_usuario(page).fill(usuario.username)
    campo_clave(page).fill(clave)
    boton_ingresar(page).click()


def con_pantalla(page, ancho, tema):
    """Ancho de la ventana y preferencia de tema del sistema (``prefers-color-scheme``)."""
    page.set_viewport_size({"width": ancho, "height": ALTO})
    page.emulate_media(color_scheme=tema)


def revisar_con_axe(page, nombre):
    """Falla ante infracciones ``critical`` o ``serious`` y guarda el informe en test-results/."""
    page.evaluate("document.fonts.ready")
    page.add_script_tag(path=str(AXE))
    resultado = page.evaluate(
        "(etiquetas) => axe.run(document, { runOnly: { type: 'tag', values: etiquetas } })",
        ETIQUETAS,
    )

    graves = [v for v in resultado["violations"] if v["impact"] in IMPACTOS_QUE_FALLAN]
    if graves:
        INFORMES.mkdir(exist_ok=True)
        informe = INFORMES / f"accesibilidad-{nombre}.json"
        informe.write_text(json.dumps(graves, ensure_ascii=False, indent=2), encoding="utf-8")
        resumen = [
            f"{v['id']} ({v['impact']}): {[nodo['target'] for nodo in v['nodes']]}" for v in graves
        ]
        pytest.fail(f"axe: {len(graves)} infracciones, informe en {informe}\n" + "\n".join(resumen))


def envejecer_sesion(page, minutos):
    """Retrasa la marca de actividad de la sesión del navegador, sin esperar 60 minutos (RN-025)."""
    clave_de_sesion = next(c["value"] for c in page.context.cookies() if c["name"] == "sessionid")
    sesion = SessionStore(session_key=clave_de_sesion)
    sesion["ultima_actividad"] = (timezone.now() - timedelta(minutes=minutos)).timestamp()
    sesion.save()
