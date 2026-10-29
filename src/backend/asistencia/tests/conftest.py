"""Datos ficticios de las pruebas de asistencia: reutiliza los de institucion (DoD 8)."""

import datetime

import pytest

from institucion.models import Estudiante
from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas


@pytest.fixture
def estudiante(seccion):
    return Estudiante.objects.create(seccion=seccion, apellidos="QUISPE MAMANI", nombres="ANA")


@pytest.fixture
def fecha():
    return datetime.date(2026, 10, 28)
