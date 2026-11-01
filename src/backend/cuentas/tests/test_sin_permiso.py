"""Página y respuesta de «sin permiso» (spec acceso-secciones; design de US-004, D3)."""

from html import unescape

import pytest
from django.test import RequestFactory
from django.urls import reverse

from actividad.models import Operacion, RegistroActividad
from cuentas.acceso import sin_permiso

pytestmark = pytest.mark.django_db

URL = "/docente/sin-permiso/"
TITULO = "No tienes permiso para ver esta sección"
TEXTO = "Vuelve a tu inicio para abrir tu sección."


def test_sin_permiso_la_ruta(db):
    assert reverse("docente:sin_permiso") == URL


def test_sin_permiso_la_docente_ve_el_mensaje_sin_crear_entrada(client, docente):
    client.force_login(docente)

    respuesta = client.get(URL)

    contenido = unescape(respuesta.content.decode())
    assert respuesta.status_code == 200
    assert TITULO in contenido
    assert TEXTO in contenido
    assert 'href="/docente/"' in contenido
    assert "Volver a tu inicio" in contenido
    assert "Sin permiso · CarpetaDocente" in contenido
    assert not RegistroActividad.objects.filter(operacion=Operacion.INTENTO_SIN_PERMISO).exists()


def test_sin_permiso_la_direccion_va_a_su_inicio(client, direccion):
    client.force_login(direccion)

    respuesta = client.get(URL)

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("direccion:inicio")


def test_sin_permiso_sin_sesion_va_al_ingreso(client):
    respuesta = client.get(URL)

    assert respuesta.status_code == 302
    assert respuesta.url == f"/ingresar/?next={URL}"


def _peticion(docente, **cabeceras):
    peticion = RequestFactory().get("/docente/secciones/1/estudiantes/", **cabeceras)
    peticion.user = docente
    return peticion


def test_sin_permiso_respuesta_403_con_la_pagina(docente):
    respuesta = sin_permiso(_peticion(docente))

    assert respuesta.status_code == 403
    assert TITULO in unescape(respuesta.content.decode())
    assert "HX-Redirect" not in respuesta


def test_sin_permiso_respuesta_htmx_403_con_hx_redirect_y_sin_cuerpo(docente):
    respuesta = sin_permiso(_peticion(docente, HTTP_HX_REQUEST="true"))

    assert respuesta.status_code == 403
    assert respuesta["HX-Redirect"] == URL
    assert respuesta.content == b""
