"""Pruebas de la carga del catálogo al migrar (spec catalogo-curricular; design de EN-06, D2 a D4).

Los textos esperados son constantes propias, copiadas del registro de notas del SIAGIE: el
archivo no se sube al repositorio.
"""

from importlib import import_module

import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from catalogo.models import Area, Competencia, InstitucionArea

pytestmark = pytest.mark.django_db

migracion = import_module("catalogo.migrations.0002_catalogo_siagie")

AREAS = [
    ("0001", "Arte y Cultura"),
    ("0002", "Castellano como segunda lengua"),
    ("0003", "Inglés como lengua extranjera"),
    ("0004", "Ciencia y Tecnología"),
    ("0005", "Comunicación"),
    ("031", "Educación Física"),
    ("035", "Educación Religiosa"),
    ("063", "Matemática"),
    ("067", "Personal Social"),
    ("0006", "Se desenvuelve en entornos virtuales generados por las TIC"),
    ("0007", "Gestiona su aprendizaje de manera autónoma"),
]

COMPETENCIAS_POR_AREA = {
    "0001": 2,
    "0002": 3,
    "0003": 3,
    "0004": 3,
    "0005": 3,
    "031": 3,
    "035": 2,
    "063": 4,
    "067": 5,
    "0006": 1,
    "0007": 1,
}

ANTES = ("catalogo", "0001_initial")
DESPUES = ("catalogo", "0002_catalogo_siagie")


def nombres_de(codigo):
    return list(
        Competencia.objects.filter(area__codigo_siagie=codigo)
        .order_by("orden")
        .values_list("nombre", flat=True)
    )


def test_once_areas_con_codigo_nombre_y_orden():
    areas = list(Area.objects.order_by("orden").values_list("codigo_siagie", "nombre", "orden"))

    assert areas == [(codigo, nombre, i) for i, (codigo, nombre) in enumerate(AREAS, start=1)]


def test_treinta_competencias_activas_con_los_conteos_por_area():
    conteos = {area.codigo_siagie: area.competencias.count() for area in Area.objects.all()}

    assert conteos == COMPETENCIAS_POR_AREA
    assert Competencia.objects.count() == 30
    assert not Competencia.objects.filter(activa=False).exists()


def test_orden_de_competencias_es_01_a_n_en_cada_area():
    for area in Area.objects.all():
        ordenes = list(area.competencias.order_by("orden").values_list("orden", flat=True))
        assert ordenes == list(range(1, len(ordenes) + 1)), area.codigo_siagie


def test_arte_y_cultura_va_en_el_orden_del_siagie():
    assert nombres_de("0001") == [
        "Aprecia de manera crítica manifestaciones artístico-culturales",
        "Crea proyectos desde los lenguajes artísticos",
    ]


def test_competencia_01_de_comunicacion_con_el_texto_de_la_leyenda():
    assert nombres_de("0005")[0] == "Se comunica oralmente en su lengua materna"


def test_gestiona_su_aprendizaje_en_minuscula():
    assert nombres_de("0007") == ["Gestiona su aprendizaje de manera autónoma"]


def test_competencias_con_su_texto_completo():
    assert nombres_de("035")[0].startswith("Construye su identidad como persona humana")
    assert nombres_de("0004")[1].endswith("biodiversidad, Tierra y Universo")
    assert nombres_de("067")[4] == "Gestiona responsablemente los recursos económicos"


def test_solo_educacion_fisica_y_religiosa_admiten_exoneracion():
    exonerables = set(Area.objects.filter(admite_exoneracion=True).values_list("nombre", flat=True))

    assert exonerables == {"Educación Física", "Educación Religiosa"}


def test_solo_los_bloques_0006_y_0007_son_transversales():
    transversales = set(
        Area.objects.filter(es_transversal=True).values_list("codigo_siagie", flat=True)
    )

    assert transversales == {"0006", "0007"}


def test_repetir_la_carga_no_duplica_ni_restaura_lo_editado():
    area = Area.objects.get(codigo_siagie="063")
    area.orden = 1
    area.save()
    competencia = Competencia.objects.get(area__codigo_siagie="0005", orden=2)
    competencia.orden = 9
    competencia.activa = False
    competencia.save()

    migracion.cargar_catalogo(apps, None)

    assert Area.objects.count() == 11
    assert Competencia.objects.count() == 30
    area.refresh_from_db()
    competencia.refresh_from_db()
    assert area.orden == 1
    assert competencia.orden == 9
    assert competencia.activa is False


def test_institucion_existente_al_migrar_recibe_sus_areas():
    executor = MigrationExecutor(connection)
    executor.migrate([ANTES])
    historicas = executor.loader.project_state([ANTES]).apps
    institucion = historicas.get_model("institucion", "Institucion").objects.create(
        nombre="I.E. Ficticia N.° 1"
    )

    MigrationExecutor(connection).migrate([DESPUES])

    filas = InstitucionArea.objects.filter(institucion_id=institucion.pk)
    assert filas.count() == 11
    assert list(filas.filter(se_trabaja=False).values_list("area__codigo_siagie", flat=True)) == [
        "0002"
    ]


def test_repetir_la_carga_no_cambia_las_areas_de_una_institucion():
    executor = MigrationExecutor(connection)
    executor.migrate([ANTES])
    historicas = executor.loader.project_state([ANTES]).apps
    institucion = historicas.get_model("institucion", "Institucion").objects.create(
        nombre="I.E. Ficticia N.° 1"
    )
    MigrationExecutor(connection).migrate([DESPUES])
    InstitucionArea.objects.filter(
        institucion_id=institucion.pk, area__codigo_siagie="0002"
    ).update(se_trabaja=True)

    migracion.cargar_catalogo(apps, None)

    filas = InstitucionArea.objects.filter(institucion_id=institucion.pk)
    assert filas.count() == 11
    assert not filas.filter(se_trabaja=False).exists()


@pytest.fixture
def catalogo_vacio():
    """Como lo deja una prueba transaccional al terminar: sin catálogo."""
    InstitucionArea.objects.all().delete()
    Competencia.objects.all().delete()
    Area.objects.all().delete()


def test_fixture_catalogo_lo_vuelve_a_cargar(catalogo_vacio, catalogo):
    assert Area.objects.count() == 11
    assert Competencia.objects.count() == 30
