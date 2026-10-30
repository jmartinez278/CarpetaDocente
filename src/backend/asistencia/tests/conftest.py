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


# Los 25 estudiantes ficticios del boceto (prototipos-cd/decision-final), ya en orden de lista.
NOMBRES_DEL_BOCETO = [
    ("AGUILAR FLORES", "LUCIANA"),
    ("ALARCÓN HUAMÁN", "DIEGO ALONSO"),
    ("ALVARADO ROJAS", "MARÍA FERNANDA"),
    ("CÁRDENAS QUISPE", "JOSÉ LUIS"),
    ("CASTILLO HUAMÁN", "CAMILA"),
    ("CHÁVEZ CONDORI", "MATEO"),
    ("CONDORI MAMANI", "DANIELA"),
    ("CRUZ HUAMÁN", "SEBASTIÁN"),
    ("FLORES SALAZAR", "VALERIA"),
    ("GARCÍA ROJAS", "ADRIÁN"),
    ("GÓMEZ TORRES", "ANTONELLA"),
    ("GONZALES RAMOS", "BRUNO"),
    ("GUTIÉRREZ SOTO", "THIAGO"),
    ("HUAMÁN QUISPE", "SOFÍA"),
    ("MAMANI ROJAS", "PAOLA"),
    ("MEDINA CASTRO", "GABRIEL"),
    ("MENDOZA DÍAZ", "LUCAS"),
    ("QUISPE MAMANI", "ANA LUCÍA"),
    ("RAMÍREZ FLORES", "LUIS MIGUEL"),
    ("RAMOS HUAMÁN", "VALENTÍN"),
    ("ROJAS MEDINA", "ISABELLA"),
    ("SALAZAR QUISPE", "EMILIA"),
    ("SÁNCHEZ VARGAS", "JOSÉ ANTONIO"),
    ("TORRES PAREDES", "ALEJANDRA"),
    ("VARGAS GUTIÉRREZ", "SANTIAGO"),
]


@pytest.fixture
def veinticinco(seccion):
    """La sección del boceto: 25 estudiantes activos, en orden de lista."""
    return [
        Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres=nombres)
        for apellidos, nombres in NOMBRES_DEL_BOCETO
    ]
