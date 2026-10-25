"""Pruebas del cierre de sesión y de las pantallas sin caché (spec cierre-sesion).

Una prueba por escenario, con el cliente de Django y cuentas ficticias.
"""

import pytest
from django.contrib.auth import SESSION_KEY
from django.test import Client

pytestmark = pytest.mark.django_db

INGRESAR = "/ingresar/"
SALIR = "/salir/"


def avisos(respuesta):
    return list(respuesta.context["messages"]) if respuesta.context else []


def test_post_cierra_la_sesion_y_lleva_a_ingresar_sin_aviso(client, docente):
    client.force_login(docente)

    respuesta = client.post(SALIR, follow=True)

    assert respuesta.redirect_chain == [(INGRESAR, 302)]
    assert SESSION_KEY not in client.session
    assert avisos(respuesta) == []


def test_la_direccion_tambien_cierra_sesion(client, direccion):
    client.force_login(direccion)

    respuesta = client.post(SALIR)

    assert respuesta["Location"] == INGRESAR
    assert SESSION_KEY not in client.session


def test_get_responde_405_y_deja_la_sesion(client, docente):
    client.force_login(docente)

    respuesta = client.get(SALIR)

    assert respuesta.status_code == 405
    assert SESSION_KEY in client.session


def test_post_sin_token_csrf_se_rechaza_y_deja_la_sesion(docente):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(docente)

    respuesta = cliente.post(SALIR)

    assert respuesta.status_code == 403
    assert SESSION_KEY in cliente.session


def test_post_sin_sesion_lleva_a_ingresar(client):
    respuesta = client.post(SALIR)

    assert respuesta.status_code == 302
    assert respuesta["Location"] == INGRESAR


def test_el_cierre_del_panel_lleva_a_ingresar(client, administrador):
    client.force_login(administrador)

    respuesta = client.post("/admin/logout/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == INGRESAR
    assert SESSION_KEY not in client.session


@pytest.mark.parametrize("ruta", ["/docente/", "/direccion/", "/admin/"])
def test_las_pantallas_con_sesion_responden_sin_cache(
    client, docente, direccion, administrador, ruta
):
    cuenta = {"/docente/": docente, "/direccion/": direccion, "/admin/": administrador}[ruta]
    client.force_login(cuenta)

    respuesta = client.get(ruta)

    assert respuesta.status_code == 200
    assert "no-store" in respuesta["Cache-Control"]


def test_despues_del_cierre_el_docente_lleva_a_ingresar_con_next(client, docente):
    client.force_login(docente)
    client.post(SALIR)

    respuesta = client.get("/docente/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == f"{INGRESAR}?next=/docente/"
