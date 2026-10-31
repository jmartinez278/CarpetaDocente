"""Dos guardados del mismo periodo a la vez, con dos conexiones (spec competencias-periodo; D5).

Escenario «Dos guardados a la vez». Cada hilo abre su propia conexión. ``serialized_rollback``
restaura el catálogo de ``catalogo/0002`` al empezar, como en ``test_demo_concurrencia.py``.
"""

import threading

import pytest
from django.db import connection

from notas import servicios
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import COMUNICACION, MATEMATICA, OCT_30, ids_de

pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)


def en_hilo(nombre, funcion, errores):
    def correr():
        try:
            funcion()
        except Exception as error:  # noqa: BLE001
            errores.append(error)
        finally:
            connection.close()

    return threading.Thread(target=correr, name=nombre)


def test_dos_guardados_a_la_vez_dejan_uno_de_los_dos_completo(
    docente, seccion_tutora, bimestres, areas_a_cargo, monkeypatch
):
    con_comunicacion = ids_de(MATEMATICA, COMUNICACION)
    solo_matematica = ids_de(MATEMATICA)
    visto = servicios.universo(docente, seccion_tutora)
    leido, seguir = threading.Event(), threading.Event()
    existentes = servicios._marcas_existentes

    def pausar(seccion, periodo, permitido):
        """El primer guardado ya leyó las marcas (ninguna): se detiene antes de escribir."""
        resultado = existentes(seccion, periodo, permitido)
        if threading.current_thread().name == "primero":
            leido.set()
            seguir.wait(5)
        return resultado

    monkeypatch.setattr(servicios, "_marcas_existentes", pausar)
    errores = []
    primero = en_hilo(
        "primero",
        lambda: servicios.guardar_marcas(
            docente, seccion_tutora, 3, con_comunicacion, OCT_30, visto=visto
        ),
        errores,
    )
    segundo = en_hilo(
        "segundo",
        lambda: servicios.guardar_marcas(
            docente, seccion_tutora, 3, solo_matematica, OCT_30, visto=visto
        ),
        errores,
    )

    primero.start()
    assert leido.wait(5)
    segundo.start()
    segundo.join(1)  # sin el bloqueo, el segundo confirma aquí, antes de que el primero escriba
    seguir.set()
    primero.join(10)
    segundo.join(10)

    assert not errores
    marcas = set(
        CompetenciaPeriodo.objects.filter(seccion=seccion_tutora, periodo__numero=3).values_list(
            "competencia_id", flat=True
        )
    )
    assert marcas in (con_comunicacion, solo_matematica)
