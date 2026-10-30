"""Carga y retiro de la demostración a la vez, con dos conexiones (spec datos-demostracion; D7, D9).

Cada hilo abre su propia conexión. ``serialized_rollback`` restaura el catálogo de ``0002`` al
empezar; al terminar, la base queda vacía y las transaccionales posteriores usan la fixture
``catalogo``.
"""

import datetime
import threading

import pytest
from django.db import connection

from cuentas.models import Usuario
from institucion import demo, servicios

pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)

HOY = datetime.date(2027, 3, 15)  # lunes


def en_hilo(funcion, errores):
    def correr():
        try:
            funcion()
        except Exception as error:  # noqa: BLE001
            errores.append(error)
        finally:
            connection.close()

    return threading.Thread(target=correr)


def test_quitar_durante_una_recarga_no_deja_cuentas_activas_sin_seccion(
    institucion, clave, monkeypatch
):
    servicios.cargar_secciones(institucion, 2027)
    demo.cargar_demo(institucion, 2, HOY, clave)
    planeado, seguir = threading.Event(), threading.Event()
    poner_clave = demo._poner_clave

    def pausar(cuenta, clave):
        """La recarga ya decidió qué hacer: se detiene antes de tocar las cuentas."""
        planeado.set()
        seguir.wait(5)
        poner_clave(cuenta, clave)

    monkeypatch.setattr(demo, "_poner_clave", pausar)
    errores = []
    recarga = en_hilo(lambda: demo.cargar_demo(institucion, 2, HOY, clave), errores)
    retiro = en_hilo(demo.quitar_demo, errores)

    recarga.start()
    assert planeado.wait(5)
    retiro.start()
    retiro.join(1)  # sin bloqueos, el retiro termina aquí, antes que la recarga
    seguir.set()
    recarga.join(10)
    retiro.join(10)

    assert not errores
    activas = set(Usuario.objects.filter(es_demo=True, is_active=True))
    assert activas == {seccion.docente for seccion in demo.secciones_demo()}


def test_primera_carga_durante_un_retiro_no_deja_secciones_con_cuentas_inactivas(
    institucion, clave, monkeypatch
):
    servicios.cargar_secciones(institucion, 2027)
    buscado, seguir = threading.Event(), threading.Event()
    borrar = demo._borrar

    def pausar(secciones):
        """El retiro ya buscó sus secciones (no había ninguna): se detiene antes de seguir."""
        buscado.set()
        seguir.wait(5)
        borrar(secciones)

    monkeypatch.setattr(demo, "_borrar", pausar)
    errores = []
    retiro = en_hilo(demo.quitar_demo, errores)
    carga = en_hilo(lambda: demo.cargar_demo(institucion, 2, HOY, clave), errores)

    retiro.start()
    assert buscado.wait(5)
    carga.start()
    carga.join(1)  # sin serializar, la carga confirma aquí, antes de que el retiro siga
    seguir.set()
    retiro.join(10)
    carga.join(10)

    assert not errores
    activas = set(Usuario.objects.filter(es_demo=True, is_active=True))
    assert activas == {seccion.docente for seccion in demo.secciones_demo()}
