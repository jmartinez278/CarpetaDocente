"""Configuración de Django para CarpetaDocente.

Toda la configuración sensible o que cambia entre entornos (laptop, vista previa
y producción) se lee de variables de entorno o del archivo ``.env`` de la raíz
del repositorio, nunca del código (documento 12, sección 6). Los nombres de las
variables están en ``.env.example``.

Referencia: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import sys
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

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

# Modo nube: Vercel define VERCEL=1 en el build y en la ejecución. No depende de
# DEBUG, porque el canal de integración corre con DJANGO_DEBUG=False (EN-02, D5).
EN_VERCEL = env.bool("VERCEL", default=False)


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
    "cuentas.middleware.InactividadMiddleware",
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


# Producción en Vercel (EN-02, D5): solo con VERCEL=1; la laptop y el canal no cambian.

if EN_VERCEL:
    # Con DEBUG=True un error 500 muestra la traza y las variables de la petición, y las
    # vistas previas se comparten con un enlace abierto: en la nube no se admite.
    if DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_DEBUG debe ser False (o no definirse) en Vercel: con True un error 500 "
            "mostraría la traza y el entorno de la petición."
        )

    # Hosts: las URL del despliegue, de su rama y de producción, sin esquema.
    _hosts_vercel = [
        host
        for host in (
            env.str(nombre, default="")
            for nombre in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")
        )
        if host
    ]
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, *_hosts_vercel]
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

    # Al detectar manage.py en la raíz, Vercel importa WSGI_APPLICATION desde la raíz
    # del repo e ignora [tool.vercel] entrypoint. Con "config.wsgi" buscaba
    # /var/task/config/wsgi.py y daba 500 (FileNotFoundError en la vista previa de 0648b72).
    WSGI_APPLICATION = "src.backend.config.wsgi.application"

    # HTTPS: el proxy de Vercel termina TLS y siempre reescribe X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # un año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Sin SECURE_HSTS_PRELOAD: sin dominio propio no hay a quién pedir la precarga y
    # vercel.app ya está en la lista de precarga del navegador. Por eso se silencia W021.
    SILENCED_SYSTEM_CHECKS = ["security.W021"]

    # La URL agrupada de Neon pasa por PgBouncer en modo transacción: sin cursores del
    # lado del servidor ni conexiones persistentes (el agrupador ya es el de Neon).
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
    DATABASES["default"]["CONN_MAX_AGE"] = 0

    # Logs a la salida estándar, que Vercel muestra en los logs de ejecución. No se
    # registran variables de entorno ni la cadena de conexión.
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "consola": {"class": "logging.StreamHandler", "stream": sys.stdout},
        },
        "loggers": {
            "django": {"handlers": ["consola"], "level": "WARNING"},
            "django.request": {"handlers": ["consola"], "level": "ERROR", "propagate": False},
        },
    }


# Usuarios y contraseñas

# Modelo de usuario propio (documento 11, sección 3.2)
AUTH_USER_MODEL = "cuentas.Usuario"

# Único backend: aplica el bloqueo por intentos de RN-024. Si ModelBackend siguiera en
# la lista, Django lo probaría después y el bloqueo se podría saltar (US-001, D1).
AUTHENTICATION_BACKENDS = ["cuentas.backends.BackendConBloqueo"]

# Pantalla de ingreso para LoginRequiredMixin y el panel (US-001, D2)
LOGIN_URL = "ingresar"
LOGOUT_REDIRECT_URL = "ingresar"


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


# Archivos de las sesiones de aprendizaje (EN-03, D2): alias propio "sesiones", sin
# tocar default ni staticfiles, para que un FileField futuro no vaya a R2 sin decidirlo.
# - Con las cuatro variables de R2: bucket privado de Cloudflare R2 (sin ACL pública y
#   con URL firmadas). En Vercel son obligatorias.
# - Fuera de Vercel y sin ellas: la carpeta media/ de la raíz, que git ignora.
# - En las pruebas: InMemoryStorage (fixture de src/backend/conftest.py).
# Los mensajes de error nombran las variables, nunca sus valores.

_VARIABLES_R2 = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_ENDPOINT_URL",
)
_r2 = {nombre: env.str(nombre, default="") for nombre in _VARIABLES_R2}
_faltan_r2 = [nombre for nombre, valor in _r2.items() if not valor]

# Fuera de Vercel, R2 a medias también se rechaza: boto3 buscaría las credenciales que
# falten en la laptop (~/.aws) sin decirlo.
if _faltan_r2 and (EN_VERCEL or len(_faltan_r2) < len(_VARIABLES_R2)):
    raise ImproperlyConfigured(
        f"Faltan variables de Cloudflare R2: {', '.join(_faltan_r2)}. "
        "En Vercel son obligatorias; fuera de Vercel van las cuatro o ninguna."
    )

if _faltan_r2:
    _ALMACEN_SESIONES = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": ROOT_DIR / "media"},
    }
else:
    _ALMACEN_SESIONES = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": _r2["AWS_ACCESS_KEY_ID"],
            "secret_key": _r2["AWS_SECRET_ACCESS_KEY"],
            "bucket_name": _r2["AWS_STORAGE_BUCKET_NAME"],
            # https://<ACCOUNT_ID>.r2.cloudflarestorage.com; R2 pide la región "auto".
            "endpoint_url": _r2["AWS_S3_ENDPOINT_URL"],
            "region_name": "auto",
            # Bucket privado: sin ACL en los objetos y solo URL firmadas, sin dominio público.
            "default_acl": None,
            "querystring_auth": True,
            "custom_domain": None,
            # La clave es única por UUID de la sesión: sobrescribir evita consultar el
            # bucket antes de cada subida.
            "file_overwrite": True,
        },
    }

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "sesiones": _ALMACEN_SESIONES,
}

# Hasta 4,5 MB (el tope de cuerpo de una función de Vercel) el archivo subido queda en
# memoria y no se escribe en /tmp (D2).
FILE_UPLOAD_MAX_MEMORY_SIZE = 4_718_592


# Claves primarias enteras de 64 bits (BIGSERIAL en el documento 11)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
