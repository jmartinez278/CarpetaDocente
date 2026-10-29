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


def test_dos_peticiones_a_10_segundos_no_modifican_la_sesion(client, docente):
    client.force_login(docente)
    envejecer(client, 0, segundos=10)
    marca = client.session[MARCA]

    for _ in range(2):
        assert client.get(PORTADA).status_code == 200

    assert client.session[MARCA] == marca


def test_a_los_30_segundos_la_marca_se_renueva(client, docente):
    client.force_login(docente)
    envejecer(client, 0, segundos=30)
    marca = client.session[MARCA]
    antes = timezone.now().timestamp()

    assert client.get(PORTADA).status_code == 200

    assert client.session[MARCA] > marca
    assert client.session[MARCA] >= antes


@pytest.mark.parametrize(("segundos", "se_renueva"), [(29, False), (30, True)])
def test_el_borde_de_los_30_segundos_con_el_reloj_congelado(
    client, docente, monkeypatch, segundos, se_renueva
):
    client.force_login(docente)
    ahora = timezone.now()
    monkeypatch.setattr(timezone, "now", lambda: ahora)
    marca = (ahora - timedelta(seconds=segundos)).timestamp()
    sesion = client.session
    sesion[MARCA] = marca
    sesion.save()

    assert client.get(PORTADA).status_code == 200

    assert client.session[MARCA] == (ahora.timestamp() if se_renueva else marca)


def test_el_ingreso_real_inicia_el_reloj_y_a_los_60_minutos_la_primera_consulta_se_rechaza(
    client, docente, clave, monkeypatch
):
    inicio = timezone.now()
    monkeypatch.setattr(timezone, "now", lambda: inicio)

    # El POST de ingreso llega como anónimo; no se sigue la redirección (cookie sí, pantalla no).
    respuesta = client.post(INGRESAR, {"username": docente.username, "password": clave})

    assert respuesta.status_code == 302
    assert client.session[MARCA] == inicio.timestamp()
    monkeypatch.setattr(timezone, "now", lambda: inicio + timedelta(minutes=60))
    consulta = client.get(PORTADA)
    assert consulta.status_code == 302
    assert consulta["Location"] == f"{INGRESAR}?next={quote(PORTADA)}"
    assert SESSION_KEY not in client.session


def test_la_primera_peticion_de_una_sesion_anterior_sin_marca_la_recibe(client, docente):
    client.force_login(docente)
    sesion = client.session
    sesion.pop(MARCA, None)
    sesion.save()
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


# --- Peticiones de HTMX (US-006, D7): el diálogo no muestra el ingreso adentro ---

HTMX = {"HTTP_HX_REQUEST": "true"}
HACIA_INGRESAR = f"{INGRESAR}?next={quote(PORTADA)}"


def test_una_peticion_htmx_vencida_responde_200_con_hx_redirect(client, docente):
    client.force_login(docente)
    envejecer(client, 60)

    respuesta = client.get("/docente/", **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == HACIA_INGRESAR
    assert respuesta.content == b""
    assert SESSION_KEY not in client.session
    assert "no-store" in respuesta["Cache-Control"]


def test_un_post_htmx_vencido_tambien_lleva_a_la_portada_como_next(client, docente):
    client.force_login(docente)
    envejecer(client, 60)

    respuesta = client.post("/docente/", **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == HACIA_INGRESAR


def test_la_peticion_htmx_vencida_deja_el_aviso_de_inactividad(client, docente):
    client.force_login(docente)
    envejecer(client, 60)
    client.get("/docente/", **HTMX)

    respuesta = client.get(INGRESAR)

    avisos = [m for m in respuesta.context["messages"] if "inactividad" in m.tags]
    assert len(avisos) == 1


def test_sin_htmx_el_302_de_siempre(client, docente):
    client.force_login(docente)
    envejecer(client, 60)

    respuesta = client.get("/docente/")

    assert respuesta.status_code == 302
    assert "HX-Redirect" not in respuesta


def test_una_peticion_htmx_sin_sesion_responde_200_con_hx_redirect(client):
    respuesta = client.get("/docente/", **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == HACIA_INGRESAR


def test_una_peticion_htmx_de_otro_rol_lleva_a_su_pantalla_con_hx_redirect(client, direccion):
    client.force_login(direccion)

    respuesta = client.get("/docente/", **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/direccion/"
