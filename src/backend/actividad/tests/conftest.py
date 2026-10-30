"""Datos ficticios de las pruebas de actividad: reutiliza los de institucion (DoD 8)."""

from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas


def quitar_inicio_de_sesion(usuario):
    """Quita la entrada INICIO_SESION que deja entrar a preparar una prueba (D4).

    Las pruebas del panel cuentan las entradas que crean; el ingreso se prueba en
    ``test_sesion.py``. ``QuerySet.delete()`` no pasa por el ``delete()`` del modelo.
    """
    from actividad.models import Operacion, RegistroActividad

    RegistroActividad.objects.filter(usuario=usuario, operacion=Operacion.INICIO_SESION).delete()


def entrar(client, usuario):
    """``force_login`` sin dejar la entrada INICIO_SESION que genera."""
    client.force_login(usuario)
    quitar_inicio_de_sesion(usuario)
    return client
