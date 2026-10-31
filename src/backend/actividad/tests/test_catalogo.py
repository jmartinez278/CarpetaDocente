"""Cada operación del catálogo tiene su prueba real (spec registro-actividad; tarea 2.6).

La tabla vive en ``escenarios.py``; lo que cada prueba deja (su operación y un detalle sin datos
personales) lo revisa el fixture ``escenario_de_operacion`` del ``conftest.py`` raíz.
"""

from importlib import import_module

import pytest

from actividad.models import RESERVADAS, Operacion
from actividad.tests.escenarios import ESCENARIOS


def test_la_tabla_cubre_el_catalogo_menos_las_reservadas():
    faltan = set(Operacion) - RESERVADAS - set(ESCENARIOS)
    sobran = set(ESCENARIOS) - (set(Operacion) - RESERVADAS)

    assert not faltan, f"operaciones sin escenario: {sorted(faltan)}"
    assert not sobran, (
        f"escenarios de operaciones reservadas o fuera del catálogo: {sorted(sobran)}"
    )


@pytest.mark.parametrize(("operacion", "escenario"), sorted(ESCENARIOS.items()))
def test_cada_escenario_es_una_prueba_que_existe(operacion, escenario):
    modulo, prueba = escenario.split("::")

    assert callable(getattr(import_module(modulo), prueba, None)), escenario
