"""Lo que ve y marca la tutora (spec competencias-periodo; design de US-029, D3)."""

import pytest

from catalogo.models import Competencia, InstitucionArea
from notas import servicios
from notas.tests.conftest import (
    CASTELLANO,
    EDUCACION_FISICA,
    INGLES,
    MATEMATICA,
)

pytestmark = pytest.mark.django_db

ORDEN_SIAGIE = [
    "Arte y Cultura",
    "Inglés como lengua extranjera",
    "Ciencia y Tecnología",
    "Comunicación",
    "Educación Física",
    "Educación Religiosa",
    "Matemática",
    "Personal Social",
    "Se desenvuelve en entornos virtuales generados por las TIC",
    "Gestiona su aprendizaje de manera autónoma",
]


def area_de(institucion, codigo):
    return InstitucionArea.objects.get(institucion=institucion, area__codigo_siagie=codigo)


# --- puede_marcar ---


def test_la_tutora_puede_marcar_un_area_que_se_trabaja(docente, seccion_tutora, institucion):
    assert servicios.puede_marcar(docente, seccion_tutora, area_de(institucion, MATEMATICA))


def test_otra_docente_no_puede_marcar(otra_docente, seccion_tutora, institucion):
    assert not servicios.puede_marcar(
        otra_docente, seccion_tutora, area_de(institucion, MATEMATICA)
    )


def test_la_direccion_no_puede_marcar(direccion, seccion_tutora, institucion):
    assert not servicios.puede_marcar(direccion, seccion_tutora, area_de(institucion, MATEMATICA))


def test_la_tutora_con_otro_rol_no_puede_marcar(docente, seccion_tutora, institucion):
    docente.rol = docente.Rol.DIRECCION

    assert not servicios.puede_marcar(docente, seccion_tutora, area_de(institucion, MATEMATICA))


def test_un_area_que_no_se_trabaja_no_se_marca(docente, seccion_tutora, institucion):
    assert not servicios.puede_marcar(docente, seccion_tutora, area_de(institucion, CASTELLANO))


def test_un_area_a_cargo_del_docente_de_curso_no_se_marca(
    docente, seccion_tutora, institucion, areas_a_cargo
):
    assert not servicios.puede_marcar(docente, seccion_tutora, area_de(institucion, INGLES))


def test_un_area_de_otra_institucion_no_se_marca(docente, seccion_tutora, otra_institucion):
    assert not servicios.puede_marcar(
        docente, seccion_tutora, area_de(otra_institucion, MATEMATICA)
    )


# --- areas_de_la_seccion y universo ---


def test_areas_de_la_seccion_en_orden_siagie_con_27_competencias_en_dos_consultas(
    docente, seccion_tutora, areas_a_cargo, django_assert_num_queries
):
    with django_assert_num_queries(2):
        areas = servicios.areas_de_la_seccion(docente, seccion_tutora)

    assert [area.area.nombre for area in areas] == ORDEN_SIAGIE
    assert sum(len(area.competencias) for area in areas) == 27
    a_cargo = {area.area.codigo_siagie for area in areas if area.a_cargo}
    assert a_cargo == {INGLES, EDUCACION_FISICA}
    assert all(area.marcable != area.a_cargo for area in areas)
    # Las transversales son áreas propias, con una competencia cada una (RN-008).
    transversales = [area for area in areas if area.area.es_transversal]
    assert [len(area.competencias) for area in transversales] == [1, 1]


def test_las_competencias_de_cada_area_van_en_su_orden(docente, seccion_tutora):
    areas = servicios.areas_de_la_seccion(docente, seccion_tutora)

    for area in areas:
        assert [c.orden for c in area.competencias] == sorted(c.orden for c in area.competencias)


def test_sin_las_competencias_inactivas(docente, seccion_tutora):
    Competencia.objects.filter(area__codigo_siagie=MATEMATICA, orden=1).update(activa=False)

    areas = servicios.areas_de_la_seccion(docente, seccion_tutora)

    (matematica,) = [area for area in areas if area.area.codigo_siagie == MATEMATICA]
    assert len(matematica.competencias) == 3


def test_el_universo_son_las_21_que_marca_la_tutora(docente, seccion_tutora, universo_ie):
    universo = servicios.universo(docente, seccion_tutora)

    assert len(universo) == 21
    assert universo == universo_ie


def test_el_universo_de_otra_docente_esta_vacio(otra_docente, seccion_tutora):
    assert servicios.universo(otra_docente, seccion_tutora) == set()


def test_el_universo_de_las_areas_no_vuelve_a_consultar(
    docente, seccion_tutora, universo_ie, django_assert_num_queries
):
    areas = servicios.areas_de_la_seccion(docente, seccion_tutora)

    with django_assert_num_queries(0):
        assert servicios.universo_de_las_areas(areas) == universo_ie


def test_universo_es_el_de_las_areas_de_la_seccion(docente, seccion_tutora):
    areas = servicios.areas_de_la_seccion(docente, seccion_tutora)

    assert servicios.universo(docente, seccion_tutora) == servicios.universo_de_las_areas(areas)
