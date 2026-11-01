"""Guardados a la vez, con dos conexiones (specs competencias-periodo y registro-notas; D5).

Escenario «Dos guardados a la vez». Cada hilo abre su propia conexión. ``serialized_rollback``
restaura el catálogo de ``catalogo/0002`` al empezar, como en ``test_demo_concurrencia.py``.
"""

import threading

import pytest
from django.db import connection

from notas import servicios
from notas.models import Calificacion, CompetenciaPeriodo
from notas.tests.conftest import (
    COMUNICACION,
    MATEMATICA,
    OCT_30,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
)

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


# --- US-020, D5: guardados de notas a la vez ---


def _pausar_el_primero(monkeypatch, leido, seguir):
    """El hilo «primero» ya leyó las notas actuales: se detiene antes de escribir."""
    actuales = servicios._notas_actuales

    def pausar(periodo, claves):
        resultado = actuales(periodo, claves)
        if threading.current_thread().name == "primero":
            leido.set()
            seguir.wait(5)
        return resultado

    monkeypatch.setattr(servicios, "_notas_actuales", pausar)


def _correr(primero, segundo, leido, seguir):
    primero.start()
    assert leido.wait(5)
    segundo.start()
    segundo.join(1)  # sin el bloqueo, el segundo confirma aquí, antes de que el primero escriba
    seguir.set()
    primero.join(10)
    segundo.join(10)


def _celda(estudiante, competencia, nivel):
    return [
        {
            "estudiante": estudiante.pk,
            "competencia": competencia,
            "nivel": nivel,
            "conclusion": "",
            "base": None,
        }
    ]


def test_dos_guardados_de_la_misma_celda_uno_guarda_y_el_otro_choca(
    docente, seccion_tutora, bimestres, areas_a_cargo, monkeypatch
):
    c1 = competencia(MATEMATICA, 1).pk
    marcar(seccion_tutora, bimestres[2], [c1])
    (ana,) = crear_estudiantes(seccion_tutora, "QUISPE, ANA")
    leido, seguir = threading.Event(), threading.Event()
    _pausar_el_primero(monkeypatch, leido, seguir)
    errores = []

    def guardar(nivel):
        return lambda: servicios.guardar_hoja(
            docente, seccion_tutora, 3, MATEMATICA, _celda(ana, c1, nivel), hoy=OCT_30
        )

    _correr(
        en_hilo("primero", guardar("A"), errores),
        en_hilo("segundo", guardar("AD"), errores),
        leido,
        seguir,
    )

    assert [type(error) for error in errores] == [servicios.NotasCambiadas]
    assert list(Calificacion.objects.values_list("nivel", flat=True)) == ["A"]


def test_notas_y_marcas_a_la_vez_nunca_dejan_una_nota_de_una_competencia_desmarcada(
    docente, seccion_tutora, bimestres, areas_a_cargo, monkeypatch
):
    c1, c2 = competencia(MATEMATICA, 1).pk, competencia(MATEMATICA, 2).pk
    marcar(seccion_tutora, bimestres[2], [c1, c2])
    (ana,) = crear_estudiantes(seccion_tutora, "QUISPE, ANA")
    visto = servicios.universo(docente, seccion_tutora)
    leido, seguir = threading.Event(), threading.Event()
    _pausar_el_primero(monkeypatch, leido, seguir)
    errores = []

    _correr(
        en_hilo(
            "primero",
            lambda: servicios.guardar_hoja(
                docente, seccion_tutora, 3, MATEMATICA, _celda(ana, c1, "A"), hoy=OCT_30
            ),
            errores,
        ),
        en_hilo(
            "segundo",
            lambda: servicios.guardar_marcas(docente, seccion_tutora, 3, [c2], OCT_30, visto=visto),
            errores,
        ),
        leido,
        seguir,
    )

    marcada = CompetenciaPeriodo.objects.filter(
        seccion=seccion_tutora, periodo=bimestres[2], competencia_id=c1
    ).exists()
    con_nota = Calificacion.objects.filter(competencia_id=c1).exists()
    assert marcada or not con_nota
    assert [type(error) for error in errores] == [servicios.CompetenciaConNotas]
