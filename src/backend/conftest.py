"""Configuración de pytest común a las pruebas de src/backend."""

import os

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
