"""Dos guardados de periodos del mismo año a la vez, con dos conexiones (design de US-028, D4).

Como en ``test_demo_concurrencia.py``: cada hilo abre su propia conexión y ``serialized_rollback``
restaura los datos de las migraciones al empezar.
"""

import datetime
import threading

import pytest
from django.db import connection

from actividad.models import Operacion, RegistroActividad
from institucion import servicios
from institucion.models import Institucion

pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)


def _filas(*rangos):
    return [
        (numero, datetime.date(2027, mi, di), datetime.date(2027, mf, df))
        for numero, ((di, mi), (df, mf)) in enumerate(rangos, start=1)
    ]


PRIMERO = _filas(((16, 3), (15, 5)), ((25, 5), (24, 7)), ((10, 8), (9, 10)), ((19, 10), (18, 12)))
# Cada rango cruza el del primero con el mismo número o el siguiente.
SEGUNDO = _filas(((1, 3), (30, 4)), ((1, 5), (15, 7)), ((1, 8), (30, 9)), ((5, 10), (20, 12)))


def en_hilo(funcion, errores):
    def correr():
        try:
            funcion()
        except Exception as error:  # noqa: BLE001
            errores.append(error)
        finally:
            connection.close()

    return threading.Thread(target=correr)


def test_dos_guardados_a_la_vez_van_en_fila_sin_integrity_error(
    anio_abierto, administrador, monkeypatch
):
    institucion = anio_abierto.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    creados, seguir = threading.Event(), threading.Event()
    comprobar = servicios._comprobar_cruce

    def pausar():
        """El primer guardado ya escribió sus filas: se detiene antes de confirmar."""
        if not creados.is_set():
            creados.set()
            seguir.wait(5)
        comprobar()

    monkeypatch.setattr(servicios, "_comprobar_cruce", pausar)
    errores = []
    primero = en_hilo(
        lambda: servicios.guardar_periodos(anio_abierto, PRIMERO, administrador), errores
    )
    segundo = en_hilo(
        lambda: servicios.guardar_periodos(anio_abierto, SEGUNDO, administrador), errores
    )

    primero.start()
    assert creados.wait(5)
    segundo.start()
    segundo.join(1)  # sin el bloqueo, el segundo ya insertó y espera el índice de uq_periodo
    seguir.set()
    primero.join(10)
    segundo.join(10)

    assert not errores
    assert list(anio_abierto.periodos.values_list("numero", "fecha_inicio", "fecha_fin")) == SEGUNDO
    operaciones = list(RegistroActividad.objects.order_by("id").values_list("operacion", flat=True))
    assert operaciones == [Operacion.PERIODOS_CONFIGURADOS] + [Operacion.PERIODO_EDITADO] * 4
