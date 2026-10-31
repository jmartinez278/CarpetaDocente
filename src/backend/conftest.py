"""Configuración de pytest común a las pruebas de src/backend."""

import os
from importlib import import_module

import pytest


@pytest.fixture(scope="session")
def django_db_modify_db_settings(django_db_modify_db_settings_parallel_suffix):
    """Una base de pruebas propia por ejecución de pytest (design.md de US-001, D13).

    Con un nombre fijo, dos pytest al mismo tiempo (``verificar.py`` y otra terminal,
    por ejemplo) chocan al crear ``test_carpetadocente`` o se la borran uno al otro.
    El sufijo es el número del proceso. Se conserva el sufijo de pytest-xdist y tox.
    """
    from django.conf import settings

    base = settings.DATABASES["default"]
    nombre = base.get("TEST", {}).get("NAME") or f"test_{base['NAME']}"
    base.setdefault("TEST", {})["NAME"] = f"{nombre}_{os.getpid()}"


@pytest.fixture
def catalogo(db):
    """Vuelve a cargar el catálogo de la migración ``catalogo/0002`` (design de EN-06, D3).

    La migración ya lo carga en la base de pruebas, pero las pruebas transaccionales (las e2e
    con ``live_server``) vacían todas las tablas al terminar, y con ellas el catálogo. Repetir
    la carga no duplica nada.
    """
    from django.apps import apps

    import_module("catalogo.migrations.0002_catalogo_siagie").cargar_catalogo(apps, None)


def _textos(valor):
    """Las cadenas de un detalle, también dentro de listas y diccionarios."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for anidado in valor.values():
            yield from _textos(anidado)
    elif isinstance(valor, list):
        for anidado in valor:
            yield from _textos(anidado)


@pytest.fixture(autouse=True)
def escenario_de_operacion(request):
    """Revisa las pruebas de ``actividad/tests/escenarios.py`` al terminar (US-008, tarea 2.6).

    Cada una debe dejar su operación, y ninguna entrada del registro puede traer en el detalle un
    nombre ficticio de estudiante ni el texto de una nota (RN-015). Las demás pruebas no se tocan.
    """
    from actividad.tests.escenarios import ESCENARIOS

    nombre = f"{request.node.module.__name__}::{request.node.originalname}"
    operaciones = [operacion for operacion, escenario in ESCENARIOS.items() if escenario == nombre]
    if not operaciones:
        yield
        return

    request.getfixturevalue("db")
    yield

    from actividad.models import RegistroActividad
    from asistencia.tests.conftest import NOMBRES_DEL_BOCETO
    from institucion import demo

    for operacion in operaciones:
        if not RegistroActividad.objects.filter(operacion=operacion).exists():
            pytest.fail(f"{nombre} no dejó {operacion}")
    prohibidos = {
        *demo.APELLIDOS,
        *demo.NOMBRES,
        demo.NOTA_JUSTIFICADO,
        *(parte for completo in NOMBRES_DEL_BOCETO for parte in completo),
        # Los de las pruebas de instrumentación.
        "QUISPE",
        "MAMANI",
        "ROJAS",
        "HUAMÁN",
        "Cita médica",
        "Viaje familiar",
    }
    for detalle in RegistroActividad.objects.values_list("detalle", flat=True):
        for texto in _textos(detalle):
            encontrados = [p for p in prohibidos if p in texto]
            if encontrados:
                pytest.fail(f"{nombre}: el detalle trae {encontrados} (RN-015)")
