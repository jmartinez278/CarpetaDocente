"""Periodos que se marcan (spec competencias-periodo; design de US-029, D4)."""

import datetime

import pytest

from institucion.models import AnioEscolar, Institucion, Periodo
from notas import servicios
from notas.tests.conftest import AGO_1, MAR_2, OCT_30

pytestmark = pytest.mark.django_db


def estados(periodos):
    return [(p.nombre, p.estado, p.editable) for p in periodos]


def test_el_30_de_octubre_el_bimestre_3_es_el_vigente(seccion_tutora, bimestres):
    periodos = servicios.periodos_de_la_seccion(seccion_tutora, OCT_30)

    assert estados(periodos) == [
        ("B1", servicios.ANTERIOR, True),
        ("B2", servicios.ANTERIOR, True),
        ("B3", servicios.VIGENTE, True),
        ("B4", servicios.FUTURO, False),
    ]
    assert [p.periodo for p in periodos] == bimestres
    assert (periodos[2].fecha_inicio, periodos[2].fecha_fin) == (
        datetime.date(2027, 8, 10),
        OCT_30,
    )
    assert periodos[2].nombre_largo == "Bimestre 3"


def test_en_un_hueco_no_hay_vigente_y_solo_los_pasados_son_editables(seccion_tutora, bimestres):
    periodos = servicios.periodos_de_la_seccion(seccion_tutora, AGO_1)

    assert estados(periodos) == [
        ("B1", servicios.ANTERIOR, True),
        ("B2", servicios.ANTERIOR, True),
        ("B3", servicios.FUTURO, False),
        ("B4", servicios.FUTURO, False),
    ]


def test_antes_del_primer_periodo_ninguno_es_editable(seccion_tutora, bimestres):
    periodos = servicios.periodos_de_la_seccion(seccion_tutora, MAR_2)

    assert [p.estado for p in periodos] == [servicios.FUTURO] * 4
    assert not any(p.editable for p in periodos)


def test_sin_periodos_la_lista_esta_vacia(seccion_tutora):
    assert servicios.periodos_de_la_seccion(seccion_tutora, OCT_30) == []


def test_en_un_anio_cerrado_ninguno_es_editable(seccion_tutora, bimestres, anio_abierto):
    AnioEscolar.objects.filter(pk=anio_abierto.pk).update(estado=AnioEscolar.Estado.CERRADO)
    seccion_tutora.anio_escolar.refresh_from_db()

    periodos = servicios.periodos_de_la_seccion(seccion_tutora, OCT_30)

    assert [p.estado for p in periodos][2] == servicios.VIGENTE
    assert not any(p.editable for p in periodos)


def test_con_trimestres_los_nombres_van_de_t1_a_t3(seccion_tutora, institucion, anio_abierto):
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()
    for numero, (inicio, fin) in enumerate(
        [((3, 9), (6, 10)), ((6, 21), (9, 10)), ((9, 20), (12, 18))], start=1
    ):
        Periodo.objects.create(
            anio_escolar=anio_abierto,
            numero=numero,
            fecha_inicio=datetime.date(2027, *inicio),
            fecha_fin=datetime.date(2027, *fin),
        )

    periodos = servicios.periodos_de_la_seccion(seccion_tutora, OCT_30)

    assert [p.nombre for p in periodos] == ["T1", "T2", "T3"]
    assert periodos[2].nombre_largo == "Trimestre 3"
    assert periodos[2].estado == servicios.VIGENTE
