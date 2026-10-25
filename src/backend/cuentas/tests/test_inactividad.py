"""Pruebas del cierre por inactividad en las peticiones (RN-025; spec cierre-sesion).

Se escribe una marca vieja en la sesión: ninguna prueba espera 60 minutos.
"""

from datetime import timedelta
from urllib.parse import quote

import pytest
from django.contrib.auth import SESSION_KEY
from django.test import Client
from django.utils import timezone

from cuentas import servicios

pytestmark = pytest.mark.django_db

INGRESAR = "/ingresar/"
PORTADA = "/docente/"
MARCA = "ultima_actividad"


def envejecer(client, minutos, segundos=0):
    sesion = client.session
    sesion[MARCA] = (timezone.now() - timedelta(minutes=minutos, seconds=segundos)).timestamp()
    sesion.save()


def test_un_get_vencido_termina_la_sesion_y_conserva_next(client, docente):
    client.force_login(docente)
    envejecer(client, 60)

    respuesta = client.get(PORTADA)

    assert respuesta.status_code == 302
    assert respuesta["Location"] == f"{INGRESAR}?next={quote(PORTADA)}"
    assert SESSION_KEY not in client.session
    assert "no-store" in respuesta["Cache-Control"]


def test_un_post_vencido_lleva_a_ingresar_sin_next(client, docente):
    client.force_login(docente)
    envejecer(client, 60)

    respuesta = client.post("/salir/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == INGRESAR
    assert SESSION_KEY not in client.session


def test_un_envio_vencido_sin_token_csrf_llega_a_ingresar_y_no_da_403(docente):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(docente)
    envejecer(cliente, 60)

    respuesta = cliente.post("/salir/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == INGRESAR
    assert SESSION_KEY not in cliente.session


def test_deja_el_aviso_con_la_etiqueta_inactividad(client, docente):
    client.force_login(docente)
    envejecer(client, 61)

    respuesta = client.get(PORTADA, follow=True)

    avisos = [m for m in respuesta.context["messages"] if "inactividad" in m.tags]
    assert len(avisos) == 1
    titulo, detalle = servicios.aviso_de_inactividad()
    assert titulo in avisos[0].message
    assert detalle in avisos[0].message


def test_a_los_59_minutos_ve_la_pantalla_y_la_marca_se_renueva(client, docente):
    client.force_login(docente)
    envejecer(client, 59)
    antes = timezone.now().timestamp()

    respuesta = client.get(PORTADA)

    assert respuesta.status_code == 200
    assert client.session[MARCA] >= antes


def test_la_primera_peticion_de_una_sesion_sin_marca_la_recibe(client, docente):
    client.force_login(docente)
    assert MARCA not in client.session

    respuesta = client.get(PORTADA)

    assert respuesta.status_code == 200
    assert MARCA in client.session


def test_el_anonimo_no_cambia(client):
    respuesta = client.get(INGRESAR)

    assert respuesta.status_code == 200
    assert MARCA not in client.session


def test_en_el_panel_la_inactividad_cierra_la_sesion(client, administrador):
    client.force_login(administrador)
    envejecer(client, 60)

    respuesta = client.get("/admin/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == f"{INGRESAR}?next={quote('/admin/')}"
    assert SESSION_KEY not in client.session


def test_en_la_direccion_la_inactividad_cierra_la_sesion(client, direccion):
    client.force_login(direccion)
    envejecer(client, 60)

    respuesta = client.get("/direccion/")

    assert respuesta.status_code == 302
    assert respuesta["Location"].startswith(INGRESAR)
    assert SESSION_KEY not in client.session
