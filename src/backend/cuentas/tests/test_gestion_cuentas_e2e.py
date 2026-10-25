"""Gestión de cuentas en el navegador (spec gestion-cuentas; design.md de US-003, D8).

El Administrador crea una docente en el panel, la docente ingresa y luego se la desactiva.
Necesita el CSS compilado y Chromium; se pide con ``uv run pytest -m e2e --browser chromium``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.models import Usuario
from cuentas.tests.e2e import abrir_ingresar, boton_ingresar, campo_clave, campo_usuario, ingresar

pytestmark = pytest.mark.e2e

MENSAJE_GENERICO = "Usuario o contraseña incorrectos, o cuenta inactiva"


def test_el_administrador_crea_una_docente_que_ingresa_y_luego_la_desactiva(
    live_server, browser, page, administrador, institucion, clave
):
    ingresar(page, live_server, administrador, clave)
    expect(page).to_have_url(f"{live_server.url}/admin/")

    page.goto(f"{live_server.url}/admin/cuentas/usuario/add/")
    page.fill("#id_first_name", "Juana")
    page.fill("#id_last_name", "Pérez")
    page.fill("#id_username", "jperez")
    page.select_option("#id_rol", "DOCENTE")
    page.select_option("#id_institucion", str(institucion.pk))
    page.fill("#id_password1", clave)
    page.fill("#id_password2", clave)
    page.get_by_role("button", name="Guardar", exact=True).click()
    expect(page.locator(".messagelist")).to_contain_text("Cuenta creada")

    # La docente ingresa desde otro navegador, escribiendo el usuario con mayúsculas.
    contexto = browser.new_context()
    docente = contexto.new_page()
    try:
        abrir_ingresar(docente, live_server)
        campo_usuario(docente).fill("JPerez")
        campo_clave(docente).fill(clave)
        boton_ingresar(docente).click()
        expect(docente).to_have_url(f"{live_server.url}/docente/")

        cuenta = Usuario.objects.get(username="jperez")
        page.goto(f"{live_server.url}/admin/cuentas/usuario/{cuenta.pk}/change/")
        page.uncheck("#id_is_active")
        page.get_by_role("button", name="Guardar", exact=True).click()
        expect(page.locator(".messagelist")).to_be_visible()

        contexto_nuevo = browser.new_context()
        otra = contexto_nuevo.new_page()
        try:
            abrir_ingresar(otra, live_server)
            campo_usuario(otra).fill("jperez")
            campo_clave(otra).fill(clave)
            boton_ingresar(otra).click()
            expect(otra).to_have_url(f"{live_server.url}/ingresar/")
            expect(otra.get_by_role("alert")).to_contain_text(MENSAJE_GENERICO)
        finally:
            contexto_nuevo.close()
    finally:
        contexto.close()
