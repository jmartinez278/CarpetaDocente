"""Configuración de Django para CarpetaDocente.

Toda la configuración sensible o que cambia entre entornos (laptop, vista previa
y producción) se lee de variables de entorno o del archivo ``.env`` de la raíz
del repositorio, nunca del código (documento 12, sección 6). Los nombres de las
variables están en ``.env.example``.

Referencia: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

import environ

# src/backend/ (proyecto Django) y raíz del repositorio (donde vive .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
)
# Las variables ya definidas en el entorno tienen prioridad sobre .env.
environ.Env.read_env(ROOT_DIR / ".env")

# Obligatoria: sin ella Django no arranca (ImproperlyConfigured).
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Desactivada si DJANGO_DEBUG no está definida.
DEBUG = env("DJANGO_DEBUG")

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")


# Aplicaciones

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Módulos del sistema (documento 12, nivel 3)
    "cuentas",
    "institucion",
    "catalogo",
    "repositorio",
    "notas",
    "asistencia",
    "direccion",
    "exportaciones",
    "actividad",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Base de datos: PostgreSQL desde DATABASE_URL (obligatoria)

DATABASES = {
    "default": env.db("DATABASE_URL"),
}
# Tiempo límite de conexión (segundos): sin él, si PostgreSQL no está levantado
# la conexión espera indefinidamente. Un connect_timeout en DATABASE_URL tiene prioridad.
DATABASES["default"].setdefault("OPTIONS", {}).setdefault("connect_timeout", 10)


# Usuarios y contraseñas

# Modelo de usuario propio (documento 11, sección 3.2)
AUTH_USER_MODEL = "cuentas.Usuario"

# Único backend: aplica el bloqueo por intentos de RN-024. Si ModelBackend siguiera en
# la lista, Django lo probaría después y el bloqueo se podría saltar (US-001, D1).
AUTHENTICATION_BACKENDS = ["cuentas.backends.BackendConBloqueo"]


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Idioma y zona horaria

LANGUAGE_CODE = "es-pe"

TIME_ZONE = "America/Lima"

USE_I18N = True

USE_TZ = True


# Archivos estáticos: fuentes en src/backend/static/ (incluye dist/, compilado
# desde src/frontend/) y destino de collectstatic en src/backend/staticfiles/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# Claves primarias enteras de 64 bits (BIGSERIAL en el documento 11)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
