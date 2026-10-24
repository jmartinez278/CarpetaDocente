"""Pruebas de la pantalla de inicio por rol y de la verificación de rol (US-001, D3)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

from cuentas.acceso import RolRequeridoMixin, pantalla_de_inicio
from cuentas.models import Usuario

pytestmark = pytest.mark.django_db


class VistaDeLaDireccion(RolRequeridoMixin, View):
    """Vista de prueba: solo la dirección la ve."""

    rol_requerido = Usuario.Rol.DIRECCION

    def get(self, request):
        return HttpResponse("contenido de la dirección")


def pedir(usuario):
    peticion = RequestFactory().get("/prueba/?filtro=1")
    peticion.user = usuario
    return VistaDeLaDireccion.as_view()(peticion)


@pytest.mark.parametrize(
    ("fixture", "destino"),
    [("docente", "/docente/"), ("direccion", "/direccion/"), ("administrador", "/admin/")],
)
def test_pantalla_de_inicio_de_cada_rol(request, fixture, destino):
    assert pantalla_de_inicio(request.getfixturevalue(fixture)) == destino


def test_sin_sesion_lleva_a_ingresar_con_next():
    respuesta = pedir(AnonymousUser())

    assert respuesta.status_code == 302
    assert respuesta.url == "/ingresar/?next=/prueba/%3Ffiltro%3D1"


def test_con_el_rol_correcto_muestra_la_vista(direccion):
    respuesta = pedir(direccion)

    assert respuesta.status_code == 200
    assert respuesta.content == b"contenido de la direcci\xc3\xb3n"


@pytest.mark.parametrize(
    ("fixture", "destino"), [("docente", "/docente/"), ("administrador", "/admin/")]
)
def test_con_otro_rol_lleva_a_su_pantalla_sin_mostrar_la_vista(request, fixture, destino):
    respuesta = pedir(request.getfixturevalue(fixture))

    assert respuesta.status_code == 302
    assert respuesta.url == destino


# --- Las dos pantallas de rol de US-001 (spec "Pantalla de inicio reservada a su rol") ---

PANTALLAS = [
    ("/docente/", "docente", {"direccion": "/direccion/", "administrador": "/admin/"}),
    ("/direccion/", "direccion", {"docente": "/docente/", "administrador": "/admin/"}),
]


@pytest.mark.parametrize(("ruta", "propio", "otros"), PANTALLAS)
def test_cada_pantalla_responde_a_su_rol(client, request, ruta, propio, otros):
    client.force_login(request.getfixturevalue(propio))

    assert client.get(ruta).status_code == 200


@pytest.mark.parametrize(
    ("ruta", "fixture", "destino"),
    [(ruta, otro, destino) for ruta, _, otros in PANTALLAS for otro, destino in otros.items()],
)
def test_cada_pantalla_lleva_a_otro_rol_a_la_suya(client, request, ruta, fixture, destino):
    client.force_login(request.getfixturevalue(fixture))

    respuesta = client.get(ruta)

    assert respuesta.status_code == 302
    assert respuesta.url == destino


@pytest.mark.parametrize("ruta", ["/docente/", "/direccion/"])
def test_cada_pantalla_sin_sesion_lleva_a_ingresar(client, ruta):
    respuesta = client.get(ruta)

    assert respuesta.status_code == 302
    assert respuesta.url == f"/ingresar/?next={ruta}"
