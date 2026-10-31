"""Pruebas de Periodo (spec periodos-anio-escolar; design de US-028, D1 y D3)."""

import datetime

import pytest
from django.db import IntegrityError, connection, transaction

from institucion.models import AnioEscolar, Periodo

pytestmark = pytest.mark.django_db


# Primera del archivo: si la base no deja crear btree_gist, falla antes que las del modelo.
def test_la_base_crea_la_extension_btree_gist():
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'btree_gist'")
        fila = cursor.fetchone()

    assert fila is not None


def _fecha(dia, mes, anio=2027):
    return datetime.date(anio, mes, dia)


def _comprobar_cruce():
    """Adelanta la comprobación de ``ex_periodo_cruce``, que es diferida (D3)."""
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ex_periodo_cruce IMMEDIATE")


@pytest.fixture
def bimestre_1(anio_abierto):
    return Periodo.objects.create(
        anio_escolar=anio_abierto, numero=1, fecha_inicio=_fecha(16, 3), fecha_fin=_fecha(15, 5)
    )


def test_numero_repetido_en_el_anio_lo_rechaza_la_base(bimestre_1):
    with pytest.raises(IntegrityError, match="uq_periodo"), transaction.atomic():
        Periodo.objects.create(
            anio_escolar=bimestre_1.anio_escolar,
            numero=1,
            fecha_inicio=_fecha(25, 5),
            fecha_fin=_fecha(24, 7),
        )


@pytest.mark.parametrize("numero", [0, 5])
def test_numero_fuera_de_rango_lo_rechaza_la_base(anio_abierto, numero):
    with pytest.raises(IntegrityError, match="ck_periodo_numero"), transaction.atomic():
        Periodo.objects.create(
            anio_escolar=anio_abierto,
            numero=numero,
            fecha_inicio=_fecha(16, 3),
            fecha_fin=_fecha(15, 5),
        )


@pytest.mark.parametrize("fin", [_fecha(16, 3), _fecha(15, 3)], ids=["igual", "anterior"])
def test_fin_no_posterior_al_inicio_lo_rechaza_la_base(anio_abierto, fin):
    with pytest.raises(IntegrityError, match="ck_periodo_fechas"), transaction.atomic():
        Periodo.objects.create(
            anio_escolar=anio_abierto, numero=1, fecha_inicio=_fecha(16, 3), fecha_fin=fin
        )


@pytest.mark.parametrize("inicio", [_fecha(1, 5), _fecha(15, 5)], ids=["dentro", "mismo-dia"])
def test_cruce_en_el_anio_lo_rechaza_la_base(bimestre_1, inicio):
    with pytest.raises(IntegrityError, match="ex_periodo_cruce"), transaction.atomic():
        Periodo.objects.create(
            anio_escolar=bimestre_1.anio_escolar,
            numero=2,
            fecha_inicio=inicio,
            fecha_fin=_fecha(24, 7),
        )
        _comprobar_cruce()


def test_mismo_rango_en_otro_anio_se_permite(bimestre_1):
    otro = AnioEscolar.objects.create(
        institucion=bimestre_1.anio_escolar.institucion, anio=2026, estado="CERRADO"
    )

    with transaction.atomic():
        Periodo.objects.create(
            anio_escolar=otro, numero=1, fecha_inicio=_fecha(16, 3), fecha_fin=_fecha(15, 5)
        )
        _comprobar_cruce()

    assert Periodo.objects.count() == 2


def test_correr_dos_periodos_en_dos_updates_no_falla(bimestre_1):
    bimestre_2 = Periodo.objects.create(
        anio_escolar=bimestre_1.anio_escolar,
        numero=2,
        fecha_inicio=_fecha(25, 5),
        fecha_fin=_fecha(24, 7),
    )

    with transaction.atomic():
        # El fin nuevo del 1 se cruza con el inicio viejo del 2 hasta el segundo UPDATE.
        Periodo.objects.filter(pk=bimestre_1.pk).update(fecha_fin=_fecha(30, 5))
        Periodo.objects.filter(pk=bimestre_2.pk).update(fecha_inicio=_fecha(8, 6))
        _comprobar_cruce()

    bimestre_1.refresh_from_db()
    bimestre_2.refresh_from_db()
    assert (bimestre_1.fecha_fin, bimestre_2.fecha_inicio) == (_fecha(30, 5), _fecha(8, 6))


def test_borrar_el_anio_borra_sus_periodos(bimestre_1):
    bimestre_1.anio_escolar.delete()

    assert not Periodo.objects.exists()


def test_periodos_ordenados_por_numero(anio_abierto):
    Periodo.objects.create(
        anio_escolar=anio_abierto, numero=2, fecha_inicio=_fecha(25, 5), fecha_fin=_fecha(24, 7)
    )
    Periodo.objects.create(
        anio_escolar=anio_abierto, numero=1, fecha_inicio=_fecha(16, 3), fecha_fin=_fecha(15, 5)
    )

    assert [p.numero for p in anio_abierto.periodos.all()] == [1, 2]
