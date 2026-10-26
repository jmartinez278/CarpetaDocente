"""Pruebas del comando cargar_secciones (spec asignacion-secciones; D5)."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.django_db


def cargar(institucion_id, anio=2027):
    salida = StringIO()
    call_command("cargar_secciones", anio=anio, institucion=institucion_id, stdout=salida)
    return salida.getvalue().strip()


def test_primera_carga_informa_lo_creado(institucion):
    mensaje = cargar(institucion.pk)

    assert mensaje == "Año 2027 creado. Secciones creadas: 24."
    assert AnioEscolar.objects.get(institucion=institucion, anio=2027).estado == "ABIERTO"
    assert Seccion.objects.filter(docente__isnull=True).count() == 24


def test_carga_repetida_informa_que_no_creo_nada(institucion):
    cargar(institucion.pk)

    mensaje = cargar(institucion.pk)

    assert mensaje == "No se creó nada: el año 2027 ya tiene sus 24 secciones."
    assert AnioEscolar.objects.count() == 1
    assert Seccion.objects.count() == 24


def test_anio_existente_informa_solo_las_secciones_creadas(anio_abierto, seccion):
    mensaje = cargar(anio_abierto.institucion_id)

    assert mensaje == "Secciones creadas: 23."


def test_anio_cerrado_termina_con_error(institucion):
    AnioEscolar.objects.create(institucion=institucion, anio=2027, estado="CERRADO")

    with pytest.raises(CommandError, match="cerrado"):
        cargar(institucion.pk)

    assert not Seccion.objects.exists()


def test_otro_anio_abierto_termina_con_error(anio_abierto):
    with pytest.raises(CommandError, match="abierto"):
        cargar(anio_abierto.institucion_id, anio=2028)

    assert AnioEscolar.objects.count() == 1
    assert not Seccion.objects.exists()


def test_institucion_inexistente_termina_con_error(db):
    with pytest.raises(CommandError, match="institución"):
        cargar(999999)

    assert not AnioEscolar.objects.exists()
