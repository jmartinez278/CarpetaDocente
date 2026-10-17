"""Pruebas de la configuración leída desde el entorno (spec entorno-desarrollo).

Cada prueba carga ``config.settings`` en un proceso aparte, con variables de
entorno controladas y sin leer el archivo ``.env`` de la laptop, para que el
resultado no dependa de la configuración local de quien ejecuta las pruebas.
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

VARIABLES_PROPIAS = (
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "DATABASE_URL",
)

ENTORNO_MINIMO = {
    "DJANGO_SECRET_KEY": "clave-ficticia-solo-para-pruebas",
    "DATABASE_URL": "postgres://usuario_ficticio:clave_ficticia@servidor-ficticio:5432/base_ficticia",
}

# Desactiva la lectura de .env antes de importar la configuración.
SIN_ARCHIVO_ENV = "import environ; environ.Env.read_env = lambda *a, **k: None; "


def cargar_settings(variables: dict[str, str], instruccion: str = "pass"):
    """Importa ``config.settings`` en un proceso nuevo con solo ``variables`` definidas."""
    entorno = {k: v for k, v in os.environ.items() if k not in VARIABLES_PROPIAS}
    entorno.pop("DJANGO_SETTINGS_MODULE", None)
    entorno.update(variables)
    codigo = SIN_ARCHIVO_ENV + "import config.settings as s; " + instruccion
    return subprocess.run(  # noqa: S603 - comando fijo, sin entrada del usuario
        [sys.executable, "-c", codigo],
        cwd=BACKEND_DIR,
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
    )


def test_debug_desactivado_si_no_se_define():
    resultado = cargar_settings(ENTORNO_MINIMO, "print(s.DEBUG)")

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "False"


def test_falta_clave_secreta_impide_arrancar():
    variables = {k: v for k, v in ENTORNO_MINIMO.items() if k != "DJANGO_SECRET_KEY"}

    resultado = cargar_settings(variables)

    assert resultado.returncode != 0
    assert "ImproperlyConfigured" in resultado.stderr
    assert "DJANGO_SECRET_KEY" in resultado.stderr


def test_falta_database_url_impide_arrancar():
    variables = {k: v for k, v in ENTORNO_MINIMO.items() if k != "DATABASE_URL"}

    resultado = cargar_settings(variables)

    assert resultado.returncode != 0
    assert "ImproperlyConfigured" in resultado.stderr
    assert "DATABASE_URL" in resultado.stderr


def test_database_url_configura_postgresql():
    resultado = cargar_settings(
        ENTORNO_MINIMO,
        "d = s.DATABASES['default']; print(d['ENGINE'], d['HOST'], d['NAME'])",
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.split() == [
        "django.db.backends.postgresql",
        "servidor-ficticio",
        "base_ficticia",
    ]


def test_conexion_a_la_base_tiene_tiempo_limite_por_defecto():
    # Sin tiempo límite, si PostgreSQL no está levantado la conexión queda
    # esperando indefinidamente en Windows en vez de fallar.
    resultado = cargar_settings(
        ENTORNO_MINIMO, "print(s.DATABASES['default']['OPTIONS']['connect_timeout'])"
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "10"


def test_tiempo_limite_de_database_url_tiene_prioridad():
    variables = {
        **ENTORNO_MINIMO,
        "DATABASE_URL": ENTORNO_MINIMO["DATABASE_URL"] + "?connect_timeout=3",
    }

    resultado = cargar_settings(
        variables, "print(s.DATABASES['default']['OPTIONS']['connect_timeout'])"
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "3"


def test_hosts_permitidos_desde_lista_separada_por_comas():
    variables = {**ENTORNO_MINIMO, "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1"}

    resultado = cargar_settings(variables, "print(s.ALLOWED_HOSTS)")

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "['localhost', '127.0.0.1']"
