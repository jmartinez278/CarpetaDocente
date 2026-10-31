"""El periodo de una fecha (spec periodos-anio-escolar, "Periodo vigente"; design de US-028, D8)."""

import datetime

import pytest
from django.utils import timezone

from institucion import servicios
from institucion.models import AnioEscolar, Periodo

pytestmark = pytest.mark.django_db


def _fecha(dia, mes):
    return datetime.date(2027, mes, dia)


@pytest.fixture
def bimestres(anio_abierto):
    rangos = [((16, 3), (15, 5)), ((25, 5), (24, 7)), ((10, 8), (9, 10)), ((19, 10), (18, 12))]
    return [
        Periodo.objects.create(
            anio_escolar=anio_abierto,
            numero=numero,
            fecha_inicio=_fecha(*inicio),
            fecha_fin=_fecha(*fin),
        )
        for numero, (inicio, fin) in enumerate(rangos, start=1)
    ]


@pytest.mark.parametrize("fecha", [_fecha(16, 3), _fecha(20, 4), _fecha(15, 5)])
def test_dentro_y_en_los_bordes_es_el_bimestre_1(bimestres, seccion, fecha):
    assert servicios.periodo_vigente(seccion, fecha) == bimestres[0]
    assert servicios.periodo_vigente(seccion.anio_escolar, fecha) == bimestres[0]


@pytest.mark.parametrize(
    "fecha",
    [_fecha(1, 8), _fecha(15, 3), _fecha(19, 12)],
    ids=["entre-2-y-3", "antes-del-1", "despues-del-4"],
)
def test_en_un_hueco_no_hay_periodo_vigente(bimestres, seccion, fecha):
    assert servicios.periodo_vigente(seccion, fecha) is None


def test_sin_periodos_no_hay_periodo_vigente(seccion):
    assert servicios.periodo_vigente(seccion, _fecha(20, 4)) is None


def test_solo_cuenta_los_periodos_de_su_anio(bimestres, institucion):
    otro = AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")

    assert servicios.periodo_vigente(otro, _fecha(20, 4)) is None


def test_sin_fecha_es_hoy_en_lima(bimestres, seccion, monkeypatch):
    """Escenario "Hoy en Lima": en UTC ya es 16 de mayo; en Lima, 15 de mayo a las 21:00."""
    utc = datetime.datetime(2027, 5, 16, 2, 0, tzinfo=datetime.UTC)
    monkeypatch.setattr(timezone, "now", lambda: utc)

    assert servicios.periodo_vigente(seccion) == bimestres[0]


def test_hace_una_sola_consulta(bimestres, seccion, django_assert_num_queries):
    with django_assert_num_queries(1):
        servicios.periodo_vigente(seccion, _fecha(20, 4))
