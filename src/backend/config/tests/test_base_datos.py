"""Prueba de que la aplicación está conectada a PostgreSQL (spec entorno-desarrollo)."""

import os

import pytest
from django.db import connection


@pytest.mark.django_db
def test_conexion_es_a_postgresql():
    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        (version,) = cursor.fetchone()

    assert connection.vendor == "postgresql"
    assert version.startswith("PostgreSQL")


@pytest.mark.django_db
def test_cada_ejecucion_de_pytest_usa_su_propia_base():
    """Dos pytest a la vez no comparten la base de pruebas (D13 de US-001)."""
    nombre = connection.settings_dict["NAME"]

    assert nombre.startswith("test_")
    assert nombre.endswith(f"_{os.getpid()}")
