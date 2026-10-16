"""Pruebas del modelo de usuario propio (spec cuentas-usuarios; documento 11, sección 3.2)."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from cuentas.models import Usuario
from institucion.models import Institucion

pytestmark = pytest.mark.django_db

CLAVE_FICTICIA = "Clave-Ficticia-2026"


@pytest.fixture
def institucion():
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


def test_modelo_de_usuario_del_proyecto_es_usuario():
    assert get_user_model() is Usuario


def test_rol_no_permitido_se_rechaza(institucion):
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.create_user(
            username="usuario_ficticio", rol="ALUMNO", institucion=institucion
        )


def test_rol_es_obligatorio(institucion):
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.create_user(username="usuario_ficticio", institucion=institucion)


@pytest.mark.parametrize("rol", [Usuario.Rol.DOCENTE, Usuario.Rol.DIRECCION])
def test_docente_o_direccion_sin_institucion_se_rechaza(rol):
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.create_user(username="usuario_ficticio", rol=rol)


def test_administrador_sin_institucion_se_acepta():
    usuario = Usuario.objects.create_user(username="admin_ficticio", rol=Usuario.Rol.ADMINISTRADOR)

    assert usuario.institucion is None


def test_docente_con_institucion_se_acepta(institucion):
    usuario = Usuario.objects.create_user(
        username="docente_ficticio", rol=Usuario.Rol.DOCENTE, institucion=institucion
    )

    assert usuario.institucion == institucion


def test_institucion_con_usuarios_no_se_elimina(institucion):
    Usuario.objects.create_user(
        username="docente_ficticio", rol=Usuario.Rol.DOCENTE, institucion=institucion
    )

    with pytest.raises(ProtectedError):
        institucion.delete()


def test_contrasena_se_guarda_con_hash(institucion):
    usuario = Usuario.objects.create_user(
        username="docente_ficticio",
        password=CLAVE_FICTICIA,
        rol=Usuario.Rol.DOCENTE,
        institucion=institucion,
    )

    usuario.refresh_from_db()
    assert usuario.password != CLAVE_FICTICIA
    assert usuario.check_password(CLAVE_FICTICIA)


def test_campos_de_control_con_valores_iniciales_sin_efecto(institucion):
    usuario = Usuario.objects.create_user(
        username="docente_ficticio", rol=Usuario.Rol.DOCENTE, institucion=institucion
    )

    usuario.refresh_from_db()
    assert usuario.debe_cambiar_password is False
    assert usuario.intentos_fallidos == 0
    assert usuario.bloqueado_hasta is None


def test_create_superuser_asigna_rol_administrador():
    usuario = Usuario.objects.create_superuser(username="admin_ficticio", password=CLAVE_FICTICIA)

    usuario.refresh_from_db()
    assert usuario.rol == Usuario.Rol.ADMINISTRADOR
    assert usuario.is_staff
    assert usuario.is_superuser


def test_create_superuser_con_otro_rol_falla():
    with pytest.raises(ValueError, match="ADMINISTRADOR"):
        Usuario.objects.create_superuser(
            username="admin_ficticio", password=CLAVE_FICTICIA, rol=Usuario.Rol.DOCENTE
        )
