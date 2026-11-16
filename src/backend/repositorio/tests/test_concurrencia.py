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
    ganadora = Sesion.objects.get()
    assert almacen.listdir("sesiones")[1] == [ganadora.archivo_clave.removeprefix("sesiones/")]


# --- Escrituras de la autora a la vez (design de US-011, D8) ---------------------------------


def _pausar_en(operacion, monkeypatch):
    """Detiene al hilo «primero» justo después de dejar ``operacion``, con la fila bloqueada."""
    original = servicios.registrar
    llego, seguir = threading.Event(), threading.Event()

    def registrar(usuario, op, **kwargs):
        resultado = original(usuario, op, **kwargs)
        if op == operacion and threading.current_thread().name == "primero":
            llego.set()
            seguir.wait(5)
        return resultado

    monkeypatch.setattr(servicios, "registrar", registrar)
    return llego, seguir


def _correr_a_la_vez(primero_fn, segundo_fn, llego, seguir):
    resultados, errores = {}, []
    primero = en_hilo("primero", primero_fn, resultados, errores)
    segundo = en_hilo("segundo", segundo_fn, resultados, errores)
    primero.start()
    assert llego.wait(5)
    segundo.start()
    segundo.join(1)
    assert segundo.is_alive(), "el segundo debía esperar el bloqueo de la fila"
    seguir.set()
    primero.join(10)
    segundo.join(10)
    return resultados, errores


def test_dos_eliminar_a_la_vez_dejan_una_entrada_y_ningun_error(docente, crear_sesion, monkeypatch):
    sesion = crear_sesion(docente, compartida=True)
    storages["sesiones"].save(sesion.archivo_clave, pdf())
    llego, seguir = _pausar_en(Operacion.SESION_ELIMINADA, monkeypatch)
    ruta = f"/docente/sesiones/{sesion.pk}/eliminar/"

    resultados, errores = _correr_a_la_vez(
        lambda: servicios.eliminar_sesion(docente, sesion.pk, ruta),
        lambda: servicios.eliminar_sesion(docente, sesion.pk, ruta),
        llego,
        seguir,
    )

    # La segunda ve «La sesión ya no está disponible»; nada más falla.
    assert [type(error) for error in errores] == [servicios.SesionNoDisponible]
    assert "primero" in resultados
    assert not Sesion.objects.exists()
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_ELIMINADA).count() == 1
    assert not RegistroActividad.objects.filter(operacion=Operacion.INTENTO_SIN_PERMISO).exists()
    assert not storages["sesiones"].exists(sesion.archivo_clave)


def test_eliminar_y_compartir_a_la_vez_nunca_comparten_una_sesion_sin_fila(
    docente, crear_sesion, monkeypatch
):
    sesion = crear_sesion(docente, compartida=False)
    llego, seguir = _pausar_en(Operacion.SESION_ELIMINADA, monkeypatch)

    resultados, errores = _correr_a_la_vez(
        lambda: servicios.eliminar_sesion(docente, sesion.pk, "/eliminar/"),
        lambda: servicios.compartir_sesion(docente, sesion.pk, True, "/compartir/"),
        llego,
        seguir,
    )

    assert [type(error) for error in errores] == [servicios.SesionNoDisponible]
    assert "segundo" not in resultados
    assert not Sesion.objects.exists()
    assert not RegistroActividad.objects.filter(operacion=Operacion.SESION_COMPARTIDA).exists()
