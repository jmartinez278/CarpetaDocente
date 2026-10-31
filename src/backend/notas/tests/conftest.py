"""Datos ficticios de las pruebas de notas: reutiliza los de institucion (DoD 8)."""

import datetime

import pytest

from catalogo.models import Competencia, InstitucionArea
from institucion.models import Institucion, Periodo
from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas

# Códigos SIAGIE de las áreas que usan las pruebas (catalogo/0002).
MATEMATICA = "063"
COMUNICACION = "0005"
ARTE = "0001"
CASTELLANO = "0002"
INGLES = "0003"
EDUCACION_FISICA = "031"

# Fechas del spec competencias-periodo: el bimestre 3 va del 10 de agosto al 30 de octubre.
BIMESTRES = [
    (datetime.date(2027, 3, 9), datetime.date(2027, 5, 15)),
    (datetime.date(2027, 5, 25), datetime.date(2027, 7, 24)),
    (datetime.date(2027, 8, 10), datetime.date(2027, 10, 30)),
    (datetime.date(2027, 11, 8), datetime.date(2027, 12, 18)),
]
OCT_30 = datetime.date(2027, 10, 30)
AGO_1 = datetime.date(2027, 8, 1)
MAR_2 = datetime.date(2027, 3, 2)
NOV_20 = datetime.date(2027, 11, 20)


def ids_de(*codigos):
    """Los id de las competencias activas de esas áreas."""
    return set(
        Competencia.objects.filter(area__codigo_siagie__in=codigos, activa=True).values_list(
            "pk", flat=True
        )
    )


@pytest.fixture
def bimestre_1(anio_abierto):
    return Periodo.objects.create(
        anio_escolar=anio_abierto,
        numero=1,
        fecha_inicio=datetime.date(2027, 3, 16),
        fecha_fin=datetime.date(2027, 5, 15),
    )


@pytest.fixture
def seccion_tutora(seccion, docente):
    """2.º A con su tutora."""
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def areas_a_cargo(institucion):
    """Educación Física e Inglés a cargo del docente de curso, como en la I.E. (decisión 12)."""
    InstitucionArea.objects.filter(
        institucion=institucion, area__codigo_siagie__in=[EDUCACION_FISICA, INGLES]
    ).update(a_cargo_docente_curso=True)


@pytest.fixture
def bimestres(institucion, anio_abierto):
    """Los 4 bimestres del spec, en una institución organizada en bimestres."""
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    return [
        Periodo.objects.create(
            anio_escolar=anio_abierto, numero=numero, fecha_inicio=inicio, fecha_fin=fin
        )
        for numero, (inicio, fin) in enumerate(BIMESTRES, start=1)
    ]


@pytest.fixture
def universo_ie(areas_a_cargo):
    """Las 21 competencias que marca la tutora en la I.E. (sin Castellano, Inglés ni E. F.)."""
    return set(
        Competencia.objects.filter(activa=True)
        .exclude(area__codigo_siagie__in=[CASTELLANO, INGLES, EDUCACION_FISICA])
        .values_list("pk", flat=True)
    )
