"""Dos guardados de periodos del mismo año a la vez, con dos conexiones (design de US-028, D4).

Como en ``test_demo_concurrencia.py``: cada hilo abre su propia conexión y ``serialized_rollback``
restaura los datos de las migraciones al empezar.
"""

import datetime
import threading

import pytest
from django.db import connection
from django.test import Client
from django.urls import reverse

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


def datos_ficha_del_anio(anio, filas):
    """POST de la ficha del año con sus periodos, sin cambiar el año (prefijo ``periodos``)."""
    datos = {
        "institucion": anio.institucion_id,
        "anio": anio.anio,
        "estado": anio.estado,
        "periodos-TOTAL_FORMS": len(filas),
        "periodos-INITIAL_FORMS": 0,
        "periodos-MIN_NUM_FORMS": 0,
        "periodos-MAX_NUM_FORMS": len(filas),
    }
    for indice, (_, inicio, fin) in enumerate(filas):
        datos[f"periodos-{indice}-fecha_inicio"] = inicio.isoformat()
        datos[f"periodos-{indice}-fecha_fin"] = fin.isoformat()
    return datos


def test_la_ficha_del_anio_y_un_guardado_a_la_vez_van_en_fila_sin_deadlock(
    anio_abierto, administrador, monkeypatch
):
    """La ficha bloquea la institución antes que el año, el mismo orden que ``guardar_periodos``.

    Si bloqueara primero el año, el otro guardado tomaría la institución y esperaría el año, y la
    ficha esperaría la institución: un deadlock que termina en un 500.
    """
    institucion = anio_abierto.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    cliente = Client()
    cliente.force_login(administrador)
    validada, seguir = threading.Event(), threading.Event()
    validar = servicios.validar_periodos

    def pausar(anio, filas):
        """La ficha ya leyó y bloqueó lo suyo y valida el formset: se detiene ahí."""
        if not validada.is_set():
            validada.set()
            seguir.wait(5)
        validar(anio, filas)

    monkeypatch.setattr(servicios, "validar_periodos", pausar)
    errores, respuestas = [], []
    url = reverse("admin:institucion_anioescolar_change", args=[anio_abierto.pk])
    ficha = en_hilo(
        lambda: respuestas.append(cliente.post(url, datos_ficha_del_anio(anio_abierto, PRIMERO))),
        errores,
    )
    guardado = en_hilo(
        lambda: servicios.guardar_periodos(anio_abierto, SEGUNDO, administrador), errores
    )

    ficha.start()
    assert validada.wait(5)
    guardado.start()
    guardado.join(1)  # espera el bloqueo que tiene la ficha
    seguir.set()
    ficha.join(10)
    guardado.join(10)

    assert not errores
    assert [respuesta.status_code for respuesta in respuestas] == [302]
    assert list(anio_abierto.periodos.values_list("numero", "fecha_inicio", "fecha_fin")) == SEGUNDO
    operaciones = list(
        RegistroActividad.objects.filter(
            operacion__in=[Operacion.PERIODOS_CONFIGURADOS, Operacion.PERIODO_EDITADO]
        )
        .order_by("id")
        .values_list("operacion", flat=True)
    )
    assert operaciones == [Operacion.PERIODOS_CONFIGURADOS] + [Operacion.PERIODO_EDITADO] * 4
