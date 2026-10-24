"""Pruebas del bloqueo por intentos fallidos (RN-024; spec inicio-sesion).

La hora se pasa como argumento: ninguna prueba espera 15 minutos ni depende del reloj.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from django.contrib.auth import hashers
from django.db import connection
from django.test.utils import CaptureQueriesContext

from cuentas import servicios
from cuentas.models import Usuario

pytestmark = pytest.mark.django_db

AHORA = datetime(2026, 10, 22, 13, 0, tzinfo=UTC)
FIN_DEL_BLOQUEO = AHORA + timedelta(minutes=15)
CLAVE_INCORRECTA = "no-es-la-clave"


def fallar(usuario, veces, ahora=AHORA):
    for _ in range(veces):
        assert servicios.intentar_ingreso(usuario, CLAVE_INCORRECTA, ahora) is False


def leer(usuario):
    return Usuario.objects.get(pk=usuario.pk)


def test_constantes_de_rn_024():
    assert servicios.INTENTOS_MAXIMOS == 5
    assert servicios.DURACION_BLOQUEO == timedelta(minutes=15)


def test_cuatro_fallos_no_bloquean(docente):
    fallar(docente, 4)

    cuenta = leer(docente)
    assert cuenta.intentos_fallidos == 4
    assert cuenta.bloqueado_hasta is None
    assert not servicios.esta_bloqueado(cuenta, AHORA)


def test_quinto_fallo_bloquea_15_minutos_y_reinicia_el_conteo(docente):
    fallar(docente, 5)

    cuenta = leer(docente)
    assert cuenta.bloqueado_hasta == FIN_DEL_BLOQUEO
    assert cuenta.intentos_fallidos == 0
    assert servicios.esta_bloqueado(cuenta, AHORA)


@pytest.mark.parametrize("correcta", [True, False], ids=["clave correcta", "clave incorrecta"])
def test_durante_el_bloqueo_nada_entra_ni_cuenta(docente, clave, correcta):
    fallar(docente, 5)
    contrasena = clave if correcta else CLAVE_INCORRECTA

    for minuto in (1, 5, 14):
        ahora = AHORA + timedelta(minutes=minuto)
        assert servicios.intentar_ingreso(docente, contrasena, ahora) is False

    cuenta = leer(docente)
    assert cuenta.bloqueado_hasta == FIN_DEL_BLOQUEO
    assert cuenta.intentos_fallidos == 0


def test_a_los_14_59_sigue_bloqueada_y_a_los_15_00_entra(docente, clave):
    fallar(docente, 5)

    assert (
        servicios.intentar_ingreso(docente, clave, FIN_DEL_BLOQUEO - timedelta(seconds=1)) is False
    )
    assert servicios.intentar_ingreso(docente, clave, FIN_DEL_BLOQUEO) is True

    cuenta = leer(docente)
    assert cuenta.bloqueado_hasta is None
    assert cuenta.intentos_fallidos == 0


def test_primer_fallo_despues_del_bloqueo_no_vuelve_a_bloquear(docente):
    fallar(docente, 5)

    fallar(docente, 1, FIN_DEL_BLOQUEO)

    cuenta = leer(docente)
    assert cuenta.intentos_fallidos == 1
    assert not servicios.esta_bloqueado(cuenta, FIN_DEL_BLOQUEO)


def test_un_ingreso_correcto_entre_fallos_reinicia_el_conteo(docente, clave):
    fallar(docente, 4)
    assert servicios.intentar_ingreso(docente, clave, AHORA) is True
    fallar(docente, 4)

    cuenta = leer(docente)
    assert cuenta.intentos_fallidos == 4
    assert cuenta.bloqueado_hasta is None


def test_cuenta_inactiva_con_la_clave_correcta_no_entra_ni_reinicia(docente, clave):
    fallar(docente, 3)
    Usuario.objects.filter(pk=docente.pk).update(is_active=False)

    assert servicios.intentar_ingreso(docente, clave, AHORA) is False

    assert leer(docente).intentos_fallidos == 3


def test_el_conteo_se_lee_de_la_base_y_no_de_una_copia_vieja(docente):
    """Dos peticiones con su propia copia de la cuenta no se pisan el conteo (select_for_update)."""
    copia_vieja = leer(docente)

    fallar(docente, 4)
    fallar(copia_vieja, 1)

    assert leer(docente).bloqueado_hasta == FIN_DEL_BLOQUEO


@pytest.fixture
def comprobaciones(monkeypatch):
    """Espía del hasher: anota, en cada comprobación, si la fila ya estaba bloqueada.

    ``al_comprobar`` corre después de la primera comprobación, en el hueco entre esta y
    el bloqueo de la fila, para simular un cambio de contraseña simultáneo.
    """
    consultas = CaptureQueriesContext(connection)
    real = hashers.verify_password
    espia = SimpleNamespace(con_la_fila_bloqueada=[], al_comprobar=None)

    def verificar(*args, **kwargs):
        espia.con_la_fila_bloqueada.append(
            any("FOR UPDATE" in consulta["sql"] for consulta in consultas.captured_queries)
        )
        resultado = real(*args, **kwargs)
        if espia.al_comprobar and len(espia.con_la_fila_bloqueada) == 1:
            espia.al_comprobar()
        return resultado

    monkeypatch.setattr(hashers, "verify_password", verificar)
    with consultas:
        yield espia


def cambiar_clave(usuario, nueva):
    Usuario.objects.filter(pk=usuario.pk).update(password=hashers.make_password(nueva))


def test_el_hash_se_calcula_antes_de_bloquear_la_fila(docente, clave, comprobaciones):
    """Sin el cálculo costoso dentro del bloqueo, una cuenta existente no se delata (hallazgo 2)."""
    assert servicios.intentar_ingreso(docente, clave, AHORA) is True

    assert comprobaciones.con_la_fila_bloqueada == [False]


def test_si_la_clave_cambia_al_comprobarla_la_vieja_no_entra(docente, clave, comprobaciones):
    comprobaciones.al_comprobar = lambda: cambiar_clave(docente, "Clave-Nueva-Ficticia")

    assert servicios.intentar_ingreso(docente, clave, AHORA) is False

    assert leer(docente).intentos_fallidos == 1


def test_si_la_clave_cambia_al_comprobarla_decide_la_vigente(docente, comprobaciones):
    comprobaciones.al_comprobar = lambda: cambiar_clave(docente, "Clave-Nueva-Ficticia")

    assert servicios.intentar_ingreso(docente, "Clave-Nueva-Ficticia", AHORA) is True


def test_un_ingreso_correcto_actualiza_un_hash_antiguo(docente, clave, settings):
    """Como ModelBackend: el hash de un hasher anterior se recalcula con el preferido."""
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    ]
    antiguo = hashers.PBKDF2SHA1PasswordHasher().encode(clave, "salficticia", iterations=1)
    Usuario.objects.filter(pk=docente.pk).update(password=antiguo)

    assert servicios.intentar_ingreso(docente, clave, AHORA) is True

    cuenta = leer(docente)
    assert cuenta.password.startswith("md5$")
    assert cuenta.check_password(clave)


def test_sin_hora_usa_la_hora_actual(docente):
    fallar(docente, 4)
    antes = datetime.now(UTC)

    assert servicios.intentar_ingreso(docente, CLAVE_INCORRECTA) is False

    cuenta = leer(docente)
    assert cuenta.bloqueado_hasta >= antes + servicios.DURACION_BLOQUEO
    assert servicios.esta_bloqueado(cuenta)


def test_desbloquear_una_cuenta_bloqueada_devuelve_true(docente, clave):
    fallar(docente, 5)

    assert servicios.desbloquear(leer(docente)) is True

    cuenta = leer(docente)
    assert cuenta.bloqueado_hasta is None
    assert cuenta.intentos_fallidos == 0
    assert servicios.intentar_ingreso(cuenta, clave, AHORA) is True


def test_desbloquear_borra_los_intentos_acumulados(docente):
    fallar(docente, 2)

    assert servicios.desbloquear(leer(docente)) is True

    assert leer(docente).intentos_fallidos == 0


def test_desbloquear_una_cuenta_sin_bloqueo_devuelve_false(docente):
    assert servicios.desbloquear(leer(docente)) is False


def test_desbloquear_usa_el_estado_vigente_y_no_una_copia_obsoleta(docente):
    """La copia se leyó antes del bloqueo: desbloquear decide con lo que dice la base."""
    copia_obsoleta = leer(docente)
    fallar(docente, 5)

    assert servicios.desbloquear(copia_obsoleta) is True

    assert leer(docente).bloqueado_hasta is None


def test_dos_copias_del_mismo_desbloqueo_dan_un_solo_exito(docente):
    fallar(docente, 5)
    primera, segunda = leer(docente), leer(docente)

    assert servicios.desbloquear(primera) is True
    assert servicios.desbloquear(segunda) is False
