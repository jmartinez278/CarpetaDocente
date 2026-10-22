"""Datos ficticios compartidos por las pruebas de cuentas (DoD 8: nada real)."""

import secrets

import pytest

from cuentas.models import Usuario
from institucion.models import Institucion


@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    """Hasher liviano: las pruebas de RN-024 calculan decenas de hashes por caso.

    PBKDF2 tarda medio segundo por hash a propósito; aquí solo importa que el hash
    se calcule, no su costo. Producción sigue con los hashers de Django (RNF-012).
    """
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def clave():
    """Contraseña generada en cada prueba, nunca escrita en el código."""
    return secrets.token_urlsafe(12)


@pytest.fixture
def institucion(db):
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


@pytest.fixture
def crear_usuario(institucion, clave):
    """Crea una cuenta ficticia del rol pedido con la contraseña de ``clave``."""

    def crear(username, rol, **campos):
        if rol != Usuario.Rol.ADMINISTRADOR:
            campos.setdefault("institucion", institucion)
        return Usuario.objects.create_user(username=username, password=clave, rol=rol, **campos)

    return crear


@pytest.fixture
def docente(crear_usuario):
    return crear_usuario("ana.quispe", Usuario.Rol.DOCENTE, first_name="Ana", last_name="Quispe")


@pytest.fixture
def direccion(crear_usuario):
    return crear_usuario(
        "rosa.huaman", Usuario.Rol.DIRECCION, first_name="Rosa", last_name="Huamán"
    )


@pytest.fixture
def administrador(crear_usuario):
    return crear_usuario(
        "admin.ficticio", Usuario.Rol.ADMINISTRADOR, is_staff=True, is_superuser=True
    )
