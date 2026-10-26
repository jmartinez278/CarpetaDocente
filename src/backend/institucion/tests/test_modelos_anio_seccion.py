"""Pruebas de AnioEscolar y Seccion (spec asignacion-secciones; documento 11, 3.1 y 3.2)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.django_db

MENSAJE_ABIERTO = "La institución ya tiene un año escolar abierto."


def test_anio_nuevo_queda_abierto(institucion):
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2027)

    anio.refresh_from_db()
    assert anio.estado == AnioEscolar.Estado.ABIERTO


def test_anio_repetido_en_la_institucion_se_rechaza(institucion):
    AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")

    with pytest.raises(IntegrityError), transaction.atomic():
        AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")


def test_segundo_anio_abierto_lo_rechaza_la_base_de_datos(anio_abierto):
    with pytest.raises(IntegrityError), transaction.atomic():
        AnioEscolar.objects.create(institucion=anio_abierto.institucion, anio=2028)


def test_segundo_anio_abierto_no_pasa_la_validacion(anio_abierto):
    nuevo = AnioEscolar(institucion=anio_abierto.institucion, anio=2028)

    with pytest.raises(ValidationError) as error:
        nuevo.full_clean()

    assert MENSAJE_ABIERTO in error.value.messages


def test_varios_anios_cerrados_y_uno_abierto_se_aceptan(institucion):
    AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")
    AnioEscolar.objects.create(institucion=institucion, anio=2027, estado="CERRADO")
    AnioEscolar.objects.create(institucion=institucion, anio=2028)

    assert institucion.anios_escolares.count() == 3


def test_otra_institucion_puede_tener_su_anio_abierto(anio_abierto, otra_institucion):
    AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)

    assert AnioEscolar.objects.filter(estado="ABIERTO").count() == 2


@pytest.mark.parametrize("anio", [2025, 2101])
def test_anio_fuera_de_rango_se_rechaza(institucion, anio):
    with pytest.raises(IntegrityError), transaction.atomic():
        AnioEscolar.objects.create(institucion=institucion, anio=anio)


def test_estado_no_permitido_se_rechaza(institucion):
    with pytest.raises(IntegrityError), transaction.atomic():
        AnioEscolar.objects.create(institucion=institucion, anio=2027, estado="PAUSADO")


def test_seccion_sin_docente_es_valida(anio_abierto):
    seccion = Seccion(anio_escolar=anio_abierto, grado=2, nombre="A")

    seccion.full_clean()
    seccion.save()
    assert seccion.docente is None


@pytest.mark.parametrize("grado", [0, 7])
def test_grado_fuera_de_rango_se_rechaza(anio_abierto, grado):
    with pytest.raises(IntegrityError), transaction.atomic():
        Seccion.objects.create(anio_escolar=anio_abierto, grado=grado, nombre="A")


def test_seccion_repetida_en_el_anio_se_rechaza(seccion):
    with pytest.raises(IntegrityError), transaction.atomic():
        Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=2, nombre="A")


def test_mismo_grado_y_nombre_en_otro_anio_se_acepta(seccion, institucion):
    seccion.anio_escolar.estado = AnioEscolar.Estado.CERRADO
    seccion.anio_escolar.save()
    otro_anio = AnioEscolar.objects.create(institucion=institucion, anio=2028)

    Seccion.objects.create(anio_escolar=otro_anio, grado=2, nombre="A")

    assert Seccion.objects.filter(grado=2, nombre="A").count() == 2


def test_borrar_el_anio_borra_sus_secciones(seccion):
    seccion.anio_escolar.delete()

    assert not Seccion.objects.exists()


def test_docente_con_seccion_no_se_puede_borrar(seccion, docente):
    seccion.docente = docente
    seccion.save()

    with pytest.raises(ProtectedError):
        docente.delete()


def test_secciones_ordenadas_por_grado_y_nombre(anio_abierto):
    for grado, nombre in [(3, "B"), (2, "B"), (2, "A")]:
        Seccion.objects.create(anio_escolar=anio_abierto, grado=grado, nombre=nombre)

    assert [(s.grado, s.nombre) for s in Seccion.objects.all()] == [(2, "A"), (2, "B"), (3, "B")]
