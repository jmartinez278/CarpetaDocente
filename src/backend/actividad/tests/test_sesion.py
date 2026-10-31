"""Inicio y cierre de sesión en el registro de actividad (design de US-008, D4).

Escenarios "Inicio y cierre de sesión", "Cierre por inactividad" y "Una lectura no deja
entrada" del spec registro-actividad. El ingreso va por ``/ingresar/`` de verdad.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad

pytestmark = pytest.mark.django_db

INGRESAR = "/ingresar/"
SALIR = "/salir/"
PORTADA = "/docente/"


def ingresar(client, usuario, contrasena):
    return client.post(INGRESAR, {"username": usuario.username, "password": contrasena})


def entradas():
    return list(
        RegistroActividad.objects.order_by("id").values("usuario_id", "operacion", "detalle")
    )


def test_ingreso_correcto_deja_inicio_sesion(client, docente, clave):
    respuesta = ingresar(client, docente, clave)

    assert respuesta.status_code == 302
    assert entradas() == [
        {"usuario_id": docente.pk, "operacion": Operacion.INICIO_SESION, "detalle": {}}
    ]


def test_cerrar_sesion_con_el_boton_deja_cierre_sesion_con_motivo_boton(client, docente, clave):
    ingresar(client, docente, clave)

    client.post(SALIR)

    assert entradas()[-1] == {
        "usuario_id": docente.pk,
        "operacion": Operacion.CIERRE_SESION,
        "detalle": {"motivo": "boton"},
    }
    assert [e["operacion"] for e in entradas()] == [
        Operacion.INICIO_SESION,
        Operacion.CIERRE_SESION,
    ]


def test_cierre_por_inactividad_deja_motivo_inactividad(client, docente, clave):
    ingresar(client, docente, clave)
    sesion = client.session
    sesion["ultima_actividad"] = (timezone.now() - timedelta(minutes=61)).timestamp()
    sesion.save()

    client.get(PORTADA)

    assert entradas()[-1] == {
        "usuario_id": docente.pk,
        "operacion": Operacion.CIERRE_SESION,
        "detalle": {"motivo": "inactividad"},
    }


def test_ingreso_rechazado_no_deja_entrada(client, docente):
    respuesta = ingresar(client, docente, "no-es-la-clave")

    assert respuesta.status_code == 200
    assert entradas() == []


def test_salir_sin_sesion_no_deja_entrada(client):
    client.post(SALIR)

    assert entradas() == []


def test_abrir_la_portada_no_deja_entrada(client, docente, clave):
    ingresar(client, docente, clave)
    antes = entradas()

    respuesta = client.get(PORTADA)

    assert respuesta.status_code == 200
    assert entradas() == antes


def test_inicio_de_sesion_y_last_login_van_en_la_misma_transaccion(
    client, docente, clave, monkeypatch
):
    """Si la entrada no puede guardarse, el ingreso tampoco: ``last_login`` queda igual (D4)."""
    from actividad import signals

    def falla(*args, **kwargs):
        raise RuntimeError("registro caído")

    monkeypatch.setattr(signals, "registrar", falla)

    with pytest.raises(RuntimeError):
        ingresar(client, docente, clave)

    docente.refresh_from_db()
    assert docente.last_login is None
    assert entradas() == []
