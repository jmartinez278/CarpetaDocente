"""Dos envíos a la vez con el mismo ``id`` (design D5; escenario «Se guardó pero no llegó la
respuesta» cuando el reintento llega antes de que el primero termine).

Cada hilo abre su propia conexión. ``serialized_rollback`` restaura el catálogo de
``catalogo/0002`` al empezar, como en ``notas/tests/test_concurrencia.py``.
"""

import threading
import uuid

import pytest
from django.core.files.storage import storages
from django.db import connection

from actividad.models import Operacion, RegistroActividad
from repositorio import servicios
from repositorio.models import Sesion
from repositorio.tests.archivos import pdf

pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)


def en_hilo(nombre, funcion, resultados, errores):
    def correr():
        try:
            resultados[nombre] = funcion()
        except Exception as error:  # noqa: BLE001
            errores.append(error)
        finally:
            connection.close()

    return threading.Thread(target=correr, name=nombre)


def test_dos_envios_con_el_mismo_id_dejan_una_sesion_y_los_dos_ven_el_exito(
    docente, comunicacion, monkeypatch
):
    datos = {
        "id": str(uuid.uuid4()),
        "grado": "2",
        "area": str(comunicacion.pk),
        "titulo": "Leemos un cuento",
    }
    almacen = storages["sesiones"]
    guardar = almacen.save
    insertado, seguir = threading.Event(), threading.Event()
    guardados = []

    def pausar(nombre, contenido, **kwargs):
        """El primero ya insertó la fila (sin confirmar): se detiene antes de guardar."""
        guardados.append(threading.current_thread().name)
        if threading.current_thread().name == "primero":
            insertado.set()
            seguir.wait(5)
        return guardar(nombre, contenido, **kwargs)

    monkeypatch.setattr(almacen, "save", pausar)
    resultados, errores = {}, []
    primero = en_hilo(
        "primero", lambda: servicios.enviar_sesion(docente, datos, pdf()), resultados, errores
    )
    segundo = en_hilo(
        "segundo", lambda: servicios.enviar_sesion(docente, datos, pdf()), resultados, errores
    )

    primero.start()
    assert insertado.wait(5)
    segundo.start()
    segundo.join(1)
    assert segundo.is_alive(), "el segundo debía esperar en la PK del primero"
    seguir.set()
    primero.join(10)
    segundo.join(10)

    assert not errores
    assert str(resultados["primero"].pk) == str(resultados["segundo"].pk) == datos["id"]
    assert Sesion.objects.count() == 1
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).count() == 1
    assert guardados == ["primero"]
    assert almacen.listdir("sesiones")[1] == [f"{datos['id']}.pdf"]
