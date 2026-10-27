"""Pruebas de la configuración leída desde el entorno (spec entorno-desarrollo).

Cada prueba carga ``config.settings`` en un proceso aparte, con variables de
entorno controladas y sin leer el archivo ``.env`` de la laptop, para que el
resultado no dependa de la configuración local de quien ejecuta las pruebas.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
RAIZ = BACKEND_DIR.parents[1]

VARIABLES_PROPIAS = (
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "DATABASE_URL",
    "VERCEL",
    "VERCEL_URL",
    "VERCEL_BRANCH_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
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


# --- Configuración de producción, solo en Vercel (spec despliegue, D5) ---

ENTORNO_VERCEL = {
    **ENTORNO_MINIMO,
    "VERCEL": "1",
    "VERCEL_URL": "carpeta-docente-abc123-equipo.vercel.app",
    "VERCEL_BRANCH_URL": "carpeta-docente-git-rama-equipo.vercel.app",
    "VERCEL_PROJECT_PRODUCTION_URL": "carpeta-docente.vercel.app",
}


def leer_settings(variables: dict[str, str], expresion: str):
    """Evalúa ``expresion`` sobre ``config.settings`` y devuelve el resultado como JSON."""
    resultado = cargar_settings(variables, f"import json; print(json.dumps({expresion}))")
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)


def test_sin_vercel_la_configuracion_queda_como_hoy():
    # El canal corre con DJANGO_DEBUG=False y sin VERCEL: nada de producción.
    variables = {**ENTORNO_MINIMO, "DJANGO_DEBUG": "False", "DJANGO_ALLOWED_HOSTS": "localhost"}

    valores = leer_settings(
        variables,
        "{'hosts': s.ALLOWED_HOSTS,"
        " 'csrf': getattr(s, 'CSRF_TRUSTED_ORIGINS', []),"
        " 'proxy': getattr(s, 'SECURE_PROXY_SSL_HEADER', None),"
        " 'redirect': getattr(s, 'SECURE_SSL_REDIRECT', False),"
        " 'sesion': getattr(s, 'SESSION_COOKIE_SECURE', False),"
        " 'csrf_cookie': getattr(s, 'CSRF_COOKIE_SECURE', False),"
        " 'hsts': getattr(s, 'SECURE_HSTS_SECONDS', 0),"
        " 'cursores': 'DISABLE_SERVER_SIDE_CURSORS' in s.DATABASES['default'],"
        " 'conn': s.DATABASES['default'].get('CONN_MAX_AGE', 0),"
        " 'logging': getattr(s, 'LOGGING', {}),"
        " 'silenciados': getattr(s, 'SILENCED_SYSTEM_CHECKS', [])}",
    )

    assert valores == {
        "hosts": ["localhost"],
        "csrf": [],
        "proxy": None,
        "redirect": False,
        "sesion": False,
        "csrf_cookie": False,
        "hsts": 0,
        "cursores": False,
        "conn": 0,
        "logging": {},
        "silenciados": [],
    }


def test_en_vercel_los_hosts_salen_de_las_variables_del_sistema():
    variables = {**ENTORNO_VERCEL, "DJANGO_ALLOWED_HOSTS": "ejemplo.test"}

    valores = leer_settings(variables, "[s.ALLOWED_HOSTS, s.CSRF_TRUSTED_ORIGINS]")

    hosts = [
        "ejemplo.test",
        "carpeta-docente-abc123-equipo.vercel.app",
        "carpeta-docente-git-rama-equipo.vercel.app",
        "carpeta-docente.vercel.app",
    ]
    assert valores == [hosts, [f"https://{host}" for host in hosts]]


def test_en_vercel_una_url_ausente_no_deja_un_host_vacio():
    variables = {k: v for k, v in ENTORNO_VERCEL.items() if k != "VERCEL_BRANCH_URL"}
    variables["VERCEL_PROJECT_PRODUCTION_URL"] = ""

    valores = leer_settings(variables, "[s.ALLOWED_HOSTS, s.CSRF_TRUSTED_ORIGINS]")

    assert valores == [
        ["carpeta-docente-abc123-equipo.vercel.app"],
        ["https://carpeta-docente-abc123-equipo.vercel.app"],
    ]


def test_en_vercel_https_detras_del_proxy_con_cookies_y_hsts():
    valores = leer_settings(
        ENTORNO_VERCEL,
        "{'proxy': s.SECURE_PROXY_SSL_HEADER,"
        " 'redirect': s.SECURE_SSL_REDIRECT,"
        " 'sesion': s.SESSION_COOKIE_SECURE,"
        " 'csrf_cookie': s.CSRF_COOKIE_SECURE,"
        " 'hsts': s.SECURE_HSTS_SECONDS,"
        " 'subdominios': s.SECURE_HSTS_INCLUDE_SUBDOMAINS,"
        " 'precarga': getattr(s, 'SECURE_HSTS_PRELOAD', False)}",
    )

    assert valores == {
        "proxy": ["HTTP_X_FORWARDED_PROTO", "https"],
        "redirect": True,
        "sesion": True,
        "csrf_cookie": True,
        "hsts": 31536000,
        "subdominios": True,
        "precarga": False,
    }


def test_en_vercel_conexion_agrupada_sin_cursores_ni_conexiones_persistentes():
    valores = leer_settings(
        ENTORNO_VERCEL,
        "{'cursores': s.DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'],"
        " 'conn': s.DATABASES['default']['CONN_MAX_AGE'],"
        " 'pool': 'pool' in s.DATABASES['default']['OPTIONS'],"
        " 'timeout': s.DATABASES['default']['OPTIONS']['connect_timeout']}",
    )

    assert valores == {"cursores": True, "conn": 0, "pool": False, "timeout": 10}


def test_en_vercel_los_logs_van_a_la_salida_estandar():
    codigo = (
        "import sys; h = s.LOGGING['handlers']['consola'];"
        " print(json.dumps({'clase': h['class'], 'stream': h['stream'] is sys.stdout,"
        " 'django': s.LOGGING['loggers']['django']['level'],"
        " 'request': s.LOGGING['loggers']['django.request']['level'],"
        " 'handlers': [s.LOGGING['loggers'][n]['handlers'] for n in ('django', 'django.request')],"
        " 'existentes': s.LOGGING['disable_existing_loggers']}))"
    )
    resultado = cargar_settings(ENTORNO_VERCEL, "import json; " + codigo)

    assert resultado.returncode == 0, resultado.stderr
    assert json.loads(resultado.stdout) == {
        "clase": "logging.StreamHandler",
        "stream": True,
        "django": "WARNING",
        "request": "ERROR",
        "handlers": [["consola"], ["consola"]],
        "existentes": False,
    }


def test_en_vercel_check_deploy_no_da_errores_ni_advertencias():
    # Depuración apagada y clave ficticia de 50 caracteres o más, como en producción.
    variables = {
        **ENTORNO_VERCEL,
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "k7Qp-ficticia-" + "x9Zr2Lm4" * 6,
    }
    codigo = (
        "import django; django.setup(); from django.core.management import call_command; "
        "call_command('check', '--deploy', '--fail-level', 'WARNING')"
    )

    resultado = cargar_settings(
        variables, "import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'; " + codigo
    )

    assert resultado.returncode == 0, resultado.stderr
    assert "WARNINGS" not in resultado.stderr


def test_en_vercel_la_depuracion_activa_impide_arrancar():
    # Con DEBUG=True un 500 mostraría la traza y las variables de la petición en una
    # URL que se comparte con "Anyone with this link".
    resultado = cargar_settings({**ENTORNO_VERCEL, "DJANGO_DEBUG": "True"})

    assert resultado.returncode != 0
    assert "ImproperlyConfigured" in resultado.stderr
    assert "DJANGO_DEBUG" in resultado.stderr


def test_sin_vercel_la_depuracion_activa_sigue_permitida():
    resultado = cargar_settings({**ENTORNO_MINIMO, "DJANGO_DEBUG": "True"}, "print(s.DEBUG)")

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "True"


def test_sin_vercel_la_entrada_wsgi_queda_como_hoy():
    assert leer_settings(ENTORNO_MINIMO, "s.WSGI_APPLICATION") == "config.wsgi.application"


def test_en_vercel_la_entrada_wsgi_se_importa_desde_la_raiz_del_repo():
    # Vercel importa WSGI_APPLICATION desde la raíz del repo (/var/task), no desde
    # src/backend/ (error real de la vista previa de 0648b72: "No such file or directory:
    # '/var/task/config/wsgi.py'").
    ruta = leer_settings(ENTORNO_VERCEL, "s.WSGI_APPLICATION")
    assert ruta == "src.backend.config.wsgi.application"

    entorno = {k: v for k, v in os.environ.items() if k not in VARIABLES_PROPIAS}
    entorno.pop("DJANGO_SETTINGS_MODULE", None)
    entorno.update(ENTORNO_VERCEL)
    codigo = (
        SIN_ARCHIVO_ENV + "from django.utils.module_loading import import_string; "
        f"print(callable(import_string({ruta!r})))"
    )
    resultado = subprocess.run(  # noqa: S603 - comando fijo, sin entrada del usuario
        [sys.executable, "-c", codigo],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "True"
