"""Pruebas del alta de usuarios en el panel de administración (rol Administrador)."""

import pytest
from django.urls import reverse

from cuentas.models import Usuario
from institucion.models import Institucion

pytestmark = pytest.mark.django_db

URL_ALTA = "admin:cuentas_usuario_add"
CLAVE_FICTICIA = "Clave-Ficticia-2026"


@pytest.fixture
def institucion():
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


def datos_alta(**cambios):
    datos = {
        "username": "docente_ficticio",
        "usable_password": "true",
        "password1": CLAVE_FICTICIA,
        "password2": CLAVE_FICTICIA,
        "rol": Usuario.Rol.DOCENTE,
    }
    datos.update(cambios)
    return datos


def test_formulario_de_alta_incluye_rol_e_institucion(admin_client):
    respuesta = admin_client.get(reverse(URL_ALTA))

    assert respuesta.status_code == 200
    campos = respuesta.context["adminform"].form.fields
    assert "rol" in campos
    assert "institucion" in campos


def test_alta_desde_el_panel_crea_docente(admin_client, institucion):
    respuesta = admin_client.post(reverse(URL_ALTA), datos_alta(institucion=institucion.pk))

    assert respuesta.status_code == 302
    usuario = Usuario.objects.get(username="docente_ficticio")
    assert usuario.rol == Usuario.Rol.DOCENTE
    assert usuario.institucion == institucion
    assert usuario.check_password(CLAVE_FICTICIA)


def test_alta_desde_el_panel_de_docente_sin_institucion_muestra_error(admin_client):
    respuesta = admin_client.post(reverse(URL_ALTA), datos_alta())

    assert respuesta.status_code == 200
    errores = respuesta.context["adminform"].form.non_field_errors()
    assert errores == ["Docente y Dirección deben pertenecer a una institución."]
    assert not Usuario.objects.filter(username="docente_ficticio").exists()
