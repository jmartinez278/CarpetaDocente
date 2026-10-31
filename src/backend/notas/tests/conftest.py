"""Datos ficticios de las pruebas de notas: reutiliza los de institucion (DoD 8)."""

import datetime

import pytest

from institucion.models import Periodo
from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas


@pytest.fixture
def bimestre_1(anio_abierto):
    return Periodo.objects.create(
        anio_escolar=anio_abierto,
        numero=1,
        fecha_inicio=datetime.date(2027, 3, 16),
        fecha_fin=datetime.date(2027, 5, 15),
    )
