"""Datos ficticios de las pruebas de exportaciones: reutiliza los de notas e institucion (DoD 8)."""

import pytest

from exportaciones import siagie
from exportaciones.tests.plantilla import CODIGO_MODULAR, generar
from institucion.models import Seccion
from notas.tests.conftest import *  # noqa: F403 - fixtures compartidas


@pytest.fixture
def ie_siagie(institucion, bimestres):
    """La I.E. con su código modular ficticio, anexo 0 y los 4 bimestres de 2027."""
    institucion.codigo_modular = CODIGO_MODULAR
    institucion.save()
    return institucion


@pytest.fixture
def secciones_de_segundo(anio_abierto, seccion):
    """2.º A (la de ``seccion``), B, C y D."""
    return [seccion] + [
        Seccion.objects.create(anio_escolar=anio_abierto, grado=2, nombre=nombre)
        for nombre in "BCD"
    ]


@pytest.fixture
def libro():
    """Abre una plantilla ficticia: ``libro(nombre_seccion="A", ...)``."""

    def abrir(**campos):
        return siagie.abrir(generar(**campos))

    return abrir
