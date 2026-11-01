"""Pruebas de CompetenciaPeriodo (US-029, D1) y Calificacion (US-020, D1)."""

import datetime

import pytest
from django.db import IntegrityError, transaction
from django.db.models import RestrictedError

from catalogo.models import Competencia
from institucion.models import Estudiante, Periodo, Seccion
from institucion.servicios import ListaConRegistros, quitar_estudiante, vaciar_lista
from notas.models import Calificacion, CompetenciaPeriodo

pytestmark = pytest.mark.django_db


@pytest.fixture
def competencia():
    return Competencia.objects.get(area__codigo_siagie="063", orden=1)


@pytest.fixture
def marca(seccion, bimestre_1, competencia):
    return CompetenciaPeriodo.objects.create(
        seccion=seccion, periodo=bimestre_1, competencia=competencia
    )


def test_la_tabla_es_competencia_periodo():
    assert CompetenciaPeriodo._meta.db_table == "competencia_periodo"


def test_la_misma_marca_dos_veces_la_rechaza_la_base(marca):
    with pytest.raises(IntegrityError, match="uq_competencia_periodo"), transaction.atomic():
        CompetenciaPeriodo.objects.create(
            seccion=marca.seccion, periodo=marca.periodo, competencia=marca.competencia
        )


def test_la_misma_competencia_en_otro_periodo_se_acepta(marca, anio_abierto):
    bimestre_2 = Periodo.objects.create(
        anio_escolar=anio_abierto,
        numero=2,
        fecha_inicio=datetime.date(2027, 5, 25),
        fecha_fin=datetime.date(2027, 7, 24),
    )

    CompetenciaPeriodo.objects.create(
        seccion=marca.seccion, periodo=bimestre_2, competencia=marca.competencia
    )

    assert CompetenciaPeriodo.objects.count() == 2


def test_borrar_el_anio_borra_sus_periodos_y_las_marcas(marca, anio_abierto):
    anio_abierto.delete()

    assert not CompetenciaPeriodo.objects.exists()
    assert not Periodo.objects.exists()
    assert not Seccion.objects.exists()


def test_borrar_la_seccion_borra_sus_marcas(marca, seccion, bimestre_1):
    seccion.delete()

    assert not CompetenciaPeriodo.objects.exists()
    assert Periodo.objects.filter(pk=bimestre_1.pk).exists()


def test_borrar_el_periodo_borra_sus_marcas(marca, seccion, bimestre_1):
    bimestre_1.delete()

    assert not CompetenciaPeriodo.objects.exists()
    assert Seccion.objects.filter(pk=seccion.pk).exists()


def test_borrar_una_competencia_con_marcas_falla(marca, competencia):
    with pytest.raises(RestrictedError), transaction.atomic():
        competencia.delete()

    assert Competencia.objects.filter(pk=competencia.pk).exists()
    assert CompetenciaPeriodo.objects.filter(pk=marca.pk).exists()


# --- Calificacion (registro-notas; design de US-020, D1) ---

CONCLUSION = "Resuelve problemas de cantidad con apoyo."


@pytest.fixture
def estudiante(seccion):
    return Estudiante.objects.create(seccion=seccion, apellidos="QUISPE", nombres="ANA")


@pytest.fixture
def nota(estudiante, bimestre_1, competencia, otra_docente):
    return Calificacion.objects.create(
        estudiante=estudiante,
        competencia=competencia,
        periodo=bimestre_1,
        nivel="A",
        registrado_por=otra_docente,
    )


def crear_nota(estudiante, periodo, competencia, nivel, conclusion=""):
    with transaction.atomic():
        return Calificacion.objects.create(
            estudiante=estudiante,
            competencia=competencia,
            periodo=periodo,
            nivel=nivel,
            conclusion_descriptiva=conclusion,
        )


def test_la_tabla_es_calificacion():
    assert Calificacion._meta.db_table == "calificacion"


def test_el_indice_es_por_periodo_y_competencia():
    indices = {indice.name: indice.fields for indice in Calificacion._meta.indexes}

    assert indices == {"idx_calificacion_periodo": ["periodo", "competencia"]}


def test_la_misma_nota_dos_veces_la_rechaza_la_base(nota):
    with pytest.raises(IntegrityError, match="uq_calificacion"):
        crear_nota(nota.estudiante, nota.periodo, nota.competencia, "B", CONCLUSION)


def test_un_nivel_fuera_de_la_escala_lo_rechaza_la_base(estudiante, bimestre_1, competencia):
    with pytest.raises(IntegrityError, match="ck_calificacion_nivel"):
        crear_nota(estudiante, bimestre_1, competencia, "15")


@pytest.mark.parametrize("nivel", ["B", "C"])
@pytest.mark.parametrize("conclusion", ["", "x" * 9, "x" * 501])
def test_b_y_c_sin_conclusion_valida_los_rechaza_la_base(
    estudiante, bimestre_1, competencia, nivel, conclusion
):
    with pytest.raises(IntegrityError, match="ck_calificacion_conclusion"):
        crear_nota(estudiante, bimestre_1, competencia, nivel, conclusion)


@pytest.mark.parametrize("nivel", ["AD", "A"])
def test_ad_y_a_con_conclusion_los_rechaza_la_base(estudiante, bimestre_1, competencia, nivel):
    with pytest.raises(IntegrityError, match="ck_calificacion_conclusion"):
        crear_nota(estudiante, bimestre_1, competencia, nivel, CONCLUSION)


@pytest.mark.parametrize("conclusion", ["x" * 10, "x" * 500])
def test_c_con_conclusion_de_10_a_500_caracteres_se_guarda(
    estudiante, bimestre_1, competencia, conclusion
):
    crear_nota(estudiante, bimestre_1, competencia, "C", conclusion)

    assert Calificacion.objects.get().conclusion_descriptiva == conclusion


def test_ad_sin_conclusion_se_guarda_vacia(estudiante, bimestre_1, competencia):
    crear_nota(estudiante, bimestre_1, competencia, "AD")

    assert Calificacion.objects.get().conclusion_descriptiva == ""


def test_borrar_un_estudiante_con_notas_falla(nota, estudiante):
    with pytest.raises(RestrictedError), transaction.atomic():
        estudiante.delete()

    assert Calificacion.objects.filter(pk=nota.pk).exists()


def test_borrar_una_competencia_con_notas_falla(nota, competencia):
    with pytest.raises(RestrictedError), transaction.atomic():
        competencia.delete()

    assert Calificacion.objects.filter(pk=nota.pk).exists()


def test_quitar_un_estudiante_con_notas_lanza_lista_con_registros(nota, estudiante):
    """Escenario «Quitar con registros» (estudiantes-seccion) con notas."""
    with pytest.raises(ListaConRegistros):
        quitar_estudiante(estudiante)

    assert Estudiante.objects.filter(pk=estudiante.pk).exists()
    assert Calificacion.objects.filter(pk=nota.pk).exists()


def test_vaciar_una_lista_con_notas_lanza_lista_con_registros(nota, seccion):
    """Escenario «Vaciar con registros» (estudiantes-seccion) con notas."""
    Estudiante.objects.create(seccion=seccion, apellidos="RAMOS", nombres="LUIS")

    with pytest.raises(ListaConRegistros):
        vaciar_lista(seccion)

    assert seccion.estudiantes.count() == 2
    assert Calificacion.objects.filter(pk=nota.pk).exists()


def test_borrar_el_periodo_borra_sus_notas(nota, bimestre_1, estudiante):
    bimestre_1.delete()

    assert not Calificacion.objects.exists()
    assert Estudiante.objects.filter(pk=estudiante.pk).exists()


def test_borrar_la_cuenta_deja_registrado_por_vacio(nota, otra_docente):
    otra_docente.delete()

    nota.refresh_from_db()
    assert nota.registrado_por is None
