"""Datos ficticios de las pruebas de repositorio: reutiliza los de institucion (DoD 8)."""

import pytest

from catalogo.models import Area
from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas

# Códigos SIAGIE de las áreas que usan las pruebas (catalogo/0002).
COMUNICACION = "0005"
MATEMATICA = "063"


@pytest.fixture
def comunicacion(db):
    return Area.objects.get(codigo_siagie=COMUNICACION)
