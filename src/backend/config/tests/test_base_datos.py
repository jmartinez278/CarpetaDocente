"""Prueba de que la aplicación está conectada a PostgreSQL (spec entorno-desarrollo)."""

import pytest
from django.db import connection


@pytest.mark.django_db
def test_conexion_es_a_postgresql():
    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        (version,) = cursor.fetchone()

    assert connection.vendor == "postgresql"
    assert version.startswith("PostgreSQL")
