"""Pruebas del backend de autenticación con bloqueo (RN-024; design.md de US-001, D1)."""

import pytest
from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth import aauthenticate, authenticate

from cuentas import servicios
from cuentas.models import Usuario

pytestmark = pytest.mark.django_db

CLAVE_INCORRECTA = "no-es-la-clave"


def bloquear(usuario):
    for _ in range(servicios.INTENTOS_MAXIMOS):
        servicios.intentar_ingreso(usuario, CLAVE_INCORRECTA)


def test_es_el_unico_backend():
    """Con ModelBackend en la lista, Django lo probaría después y RN-024 se saltaría."""
    assert settings.AUTHENTICATION_BACKENDS == ["cuentas.backends.BackendConBloqueo"]


def test_datos_correctos_devuelven_la_cuenta(docente, clave):
    assert authenticate(None, username="ana.quispe", password=clave) == docente


def test_usuario_inexistente_devuelve_none_y_calcula_el_hash(db, monkeypatch, clave):
    """El hash se calcula igual que con una cuenta real: el tiempo no delata si existe."""
    calculados = []
    original = Usuario.set_password
    monkeypatch.setattr(
        Usuario, "set_password", lambda self, raw: calculados.append(raw) or original(self, raw)
    )

    assert authenticate(None, username="nadie.ficticio", password=clave) is None
    assert calculados == [clave]


def test_cuenta_bloqueada_con_la_clave_correcta_devuelve_none(docente, clave):
    bloquear(docente)

    assert authenticate(None, username="ana.quispe", password=clave) is None


def test_cuenta_inactiva_devuelve_none(crear_usuario, clave):
    crear_usuario("inactiva.ficticia", Usuario.Rol.DOCENTE, is_active=False)

    assert authenticate(None, username="inactiva.ficticia", password=clave) is None


def test_un_fallo_por_authenticate_cuenta_como_intento(docente):
    assert authenticate(None, username="ana.quispe", password=CLAVE_INCORRECTA) is None

    docente.refresh_from_db()
    assert docente.intentos_fallidos == 1


def test_sin_contrasena_no_cuenta_un_intento(docente):
    assert authenticate(None, username="ana.quispe", password=None) is None

    docente.refresh_from_db()
    assert docente.intentos_fallidos == 0


def test_sin_usuario_devuelve_none(docente, clave):
    assert authenticate(None, password=clave) is None


def test_la_version_asincrona_tambien_respeta_el_bloqueo(docente, clave):
    """ModelBackend.aauthenticate no pasa por authenticate(): sin redefinirla, saltaría RN-024."""
    for _ in range(servicios.INTENTOS_MAXIMOS):
        async_to_sync(aauthenticate)(None, username="ana.quispe", password=CLAVE_INCORRECTA)

    resultado = async_to_sync(aauthenticate)(None, username="ana.quispe", password=clave)

    assert resultado is None
    docente.refresh_from_db()
    assert servicios.esta_bloqueado(docente)


# --- Usuario sin distinguir mayúsculas (US-003, D7) ---


@pytest.mark.parametrize("escrito", ["Ana.Quispe", "ANA.QUISPE"])
def test_el_usuario_con_mayusculas_entra_en_la_cuenta_en_minusculas(docente, clave, escrito):
    assert authenticate(None, username=escrito, password=clave) == docente


def test_cinco_fallos_con_distintas_mayusculas_bloquean_la_misma_cuenta(docente):
    for escrito in ["ana.quispe", "Ana.Quispe", "ANA.QUISPE", "ana.quispe", "Ana.QUISPE"]:
        assert authenticate(None, username=escrito, password=CLAVE_INCORRECTA) is None

    docente.refresh_from_db()
    assert docente.bloqueado_hasta is not None
