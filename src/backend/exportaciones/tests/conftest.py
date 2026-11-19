"""Datos ficticios de las pruebas de exportaciones: reutiliza los de notas e institucion (DoD 8)."""

import pytest

from exportaciones import siagie
from exportaciones.tests.plantilla import CODIGO_MODULAR, generar
from institucion.models import Seccion
from notas.tests.conftest import *  # noqa: F403 - fixtures compartidas
from notas.tests.conftest import (
    COMUNICACION,
    MATEMATICA,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)

MARIA = "PÉREZ QUISPE, MARÍA"


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


@pytest.fixture
def b3(bimestres):
    return bimestres[2]


@pytest.fixture
def notas_b3(seccion_tutora, ie_siagie, b3):
    """María con una nota de Matemática en B3, en 2.º A."""
    (maria,) = crear_estudiantes(seccion_tutora, MARIA)
    marcar(seccion_tutora, b3, ids_de(MATEMATICA, COMUNICACION))
    poner_nota(maria, competencia(MATEMATICA, 1), b3, "B")
    return b3


@pytest.fixture
def b_con_notas(secciones_de_segundo, ie_siagie, b3):
    """2.º B con una nota en B3; 2.º A, C y D no tienen estudiantes."""
    seccion_b = secciones_de_segundo[1]
    (maria,) = crear_estudiantes(seccion_b, MARIA)
    marcar(seccion_b, b3, ids_de(MATEMATICA))
    poner_nota(maria, competencia(MATEMATICA, 1), b3, "B")
    return seccion_b
