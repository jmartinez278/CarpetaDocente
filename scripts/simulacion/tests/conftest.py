"""Fixtures de las pruebas de la simulación que usan la base de Django (G2). Datos simulados."""

import os

import pytest


@pytest.fixture(scope="session")
def django_db_modify_db_settings(django_db_modify_db_settings_parallel_suffix):
    """Una base de pruebas propia por proceso, como en src/backend/conftest.py.

    Las pruebas usan siempre la base de pruebas, nunca la de desarrollo.
    """
    from django.conf import settings

    base = settings.DATABASES["default"]
    nombre = base.get("TEST", {}).get("NAME") or f"test_{base['NAME']}"
    base.setdefault("TEST", {})["NAME"] = f"{nombre}_{os.getpid()}"


@pytest.fixture(autouse=True)
def almacenamiento_en_memoria(settings):
    """Los archivos de las sesiones van a memoria: ninguna prueba escribe en media/ ni en R2."""
    settings.STORAGES = {
        **settings.STORAGES,
        "sesiones": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    }
