"""Inicio de sesión en el navegador (specs integracion-continua y pantallas-de-inicio; D10).

Recorre el escenario "Página inicial en el navegador", "Mostrar contraseña" con y sin
JavaScript y el estado de envío. Necesita el CSS compilado (``npm run build`` en
``src/frontend/``) y Chromium; se pide con ``uv run pytest -m e2e --browser chromium``.
"""

import re

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import (
    abrir_ingresar,
    boton_ingresar,
    campo_clave,
    campo_usuario,
    ingresar,
)

pytestmark = pytest.mark.e2e


def test_de_la_raiz_al_inicio_de_sesion_y_a_la_portada(live_server, page, docente, clave):
    with page.expect_response("**/static/dist/app.css") as respuesta:
        page.goto(f"{live_server.url}/")

    assert respuesta.value.status == 200
    expect(page).to_have_url(f"{live_server.url}/ingresar/")
    expect(page.get_by_role("heading", level=1)).to_have_text("I.E. Virgen del Carmen")
    expect(page.get_by_text("Sesiones · Notas · Asistencia")).to_be_visible()
    # El inicio de sesión no carga Alpine.js; cada pantalla carga solo lo que usa.
    assert page.evaluate("typeof Alpine") == "undefined"

    campo_usuario(page).fill(docente.username)
    campo_clave(page).fill(clave)
    boton_ingresar(page).click()

    expect(page).to_have_url(f"{live_server.url}/docente/")
    expect(page.get_by_role("heading", level=1)).to_have_text("Hola, Ana Quispe")
    expect(page.get_by_role("heading", level=2)).to_have_text(["Sesiones", "Notas", "Asistencia"])
    assert page.evaluate("typeof Alpine") == "object"


def test_la_direccion_llega_a_su_inicio(live_server, page, direccion, clave):
    ingresar(page, live_server, direccion, clave)

    expect(page).to_have_url(f"{live_server.url}/direccion/")
    expect(page.get_by_role("heading", level=1)).to_have_text("Hola, Rosa Huamán")


def test_mostrar_contrasena_alterna_la_vista(live_server, page, clave):
    abrir_ingresar(page, live_server)
    campo_clave(page).fill(clave)
    boton = page.get_by_role("button", name="Mostrar contraseña")

    expect(boton).to_have_attribute("aria-pressed", "false")
    expect(campo_clave(page)).to_have_attribute("type", "password")

    boton.click()
    expect(boton).to_have_attribute("aria-pressed", "true")
    expect(campo_clave(page)).to_have_attribute("type", "text")

    boton.click()
    expect(boton).to_have_attribute("aria-pressed", "false")
    expect(campo_clave(page)).to_have_attribute("type", "password")


def test_sin_javascript_no_hay_boton_y_el_formulario_se_envia(live_server, browser, docente, clave):
    contexto = browser.new_context(java_script_enabled=False)
    page = contexto.new_page()
    try:
        abrir_ingresar(page, live_server)
        expect(page.get_by_role("button", name="Mostrar contraseña")).to_have_count(0)

        campo_usuario(page).fill(docente.username)
        campo_clave(page).fill(clave)
        boton_ingresar(page).click()

        expect(page).to_have_url(f"{live_server.url}/docente/")
    finally:
        contexto.close()


def test_envio_en_curso_cambia_el_boton_y_deja_los_campos_de_solo_lectura(
    live_server, page, docente, clave
):
    abrir_ingresar(page, live_server)
    # Detiene la navegación después de que ingresar.js marca el envío (su escucha corre antes que
    # esta): así el estado "esperando la respuesta" se queda en pantalla para revisarlo.
    page.evaluate(
        "document.querySelector('[data-formulario-ingreso]')"
        ".addEventListener('submit', (evento) => evento.preventDefault())"
    )
    campo_usuario(page).fill(docente.username)
    campo_clave(page).fill(clave)
    boton_ingresar(page).click()

    boton = page.get_by_role("button", name="Ingresando…")
    expect(boton).to_be_visible()
    expect(boton).to_have_class(re.compile(r"boton-principal--enviando"))
    expect(campo_usuario(page)).to_have_attribute("readonly", "")
    expect(campo_clave(page)).to_have_attribute("readonly", "")
    expect(page).to_have_url(f"{live_server.url}/ingresar/")
