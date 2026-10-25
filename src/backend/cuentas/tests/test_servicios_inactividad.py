"""Pruebas del cierre por inactividad (RN-025, RNF-015; spec cierre-sesion).

La hora se pasa como argumento: ninguna prueba espera 60 minutos ni depende del reloj.
"""

from datetime import UTC, datetime, timedelta

from cuentas import servicios

AHORA = datetime(2026, 10, 25, 13, 0, tzinfo=UTC)


def test_constante_de_rn_025():
    assert servicios.INACTIVIDAD_MAXIMA == timedelta(minutes=60)


def test_a_los_59_minutos_con_59_segundos_no_vence():
    ultima = AHORA - timedelta(minutes=59, seconds=59)

    assert servicios.sesion_vencida(ultima.timestamp(), AHORA) is False


def test_a_los_60_minutos_vence():
    ultima = AHORA - timedelta(minutes=60)

    assert servicios.sesion_vencida(ultima.timestamp(), AHORA) is True


def test_pasados_los_60_minutos_vence():
    ultima = AHORA - timedelta(hours=3)

    assert servicios.sesion_vencida(ultima.timestamp(), AHORA) is True


def test_una_sesion_sin_marca_no_vence():
    assert servicios.sesion_vencida(None, AHORA) is False


def test_el_aviso_usa_la_duracion_de_la_constante(monkeypatch):
    titulo, detalle = servicios.aviso_de_inactividad()
    assert titulo == "Tu sesión se cerró por inactividad."
    assert detalle == "Pasaron 60 minutos sin uso. Ingresa de nuevo para continuar."

    monkeypatch.setattr(servicios, "INACTIVIDAD_MAXIMA", timedelta(minutes=45))

    assert "45 minutos" in servicios.aviso_de_inactividad()[1]
