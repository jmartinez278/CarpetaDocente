"""Pruebas de Jornada y Asistencia (spec asistencia-jornada; design de US-030, D1)."""

import datetime

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from asistencia.models import Asistencia, Jornada
from institucion.models import Estudiante

pytestmark = pytest.mark.django_db


@pytest.fixture
def jornada(seccion, docente, fecha):
    return Jornada.objects.create(seccion=seccion, fecha=fecha, registrado_por=docente)


def test_segunda_jornada_de_la_misma_seccion_y_fecha_la_rechaza_la_base(
    seccion, docente, fecha, jornada
):
    with pytest.raises(IntegrityError), transaction.atomic():
        Jornada.objects.create(seccion=seccion, fecha=fecha, registrado_por=docente)


def test_segundo_estado_del_mismo_estudiante_en_la_jornada_lo_rechaza_la_base(jornada, estudiante):
    Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")

    with pytest.raises(IntegrityError), transaction.atomic():
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="FALTO")


def test_estado_fuera_de_los_cuatro_lo_rechaza_la_base(jornada, estudiante):
    with pytest.raises(IntegrityError), transaction.atomic():
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="PERMISO")


@pytest.mark.parametrize("estado", ["ASISTIO", "FALTO", "TARDE", "JUSTIFICADO"])
def test_los_cuatro_estados_validos_se_guardan(jornada, estudiante, estado):
    asistencia = Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado=estado)

    asistencia.refresh_from_db()
    assert asistencia.estado == estado
    assert asistencia.nota_justificacion == ""


@pytest.mark.parametrize("estado", ["ASISTIO", "FALTO", "TARDE"])
def test_nota_con_estado_distinto_de_justificado_la_rechaza_la_base(jornada, estudiante, estado):
    with pytest.raises(IntegrityError), transaction.atomic():
        Asistencia.objects.create(
            jornada=jornada, estudiante=estudiante, estado=estado, nota_justificacion="Cita médica"
        )


def test_nota_con_justificado_se_guarda(jornada, estudiante):
    Asistencia.objects.create(
        jornada=jornada, estudiante=estudiante, estado="JUSTIFICADO", nota_justificacion="Cita"
    )

    assert Asistencia.objects.get().nota_justificacion == "Cita"


def test_borrar_la_seccion_borra_jornadas_y_asistencias(seccion, jornada, estudiante):
    Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")

    seccion.delete()

    assert Jornada.objects.count() == 0
    assert Asistencia.objects.count() == 0
    assert Estudiante.objects.count() == 0


def test_actualizado_en_cambia_al_actualizar(jornada, estudiante):
    asistencia = Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")
    pasado = timezone.now() - datetime.timedelta(days=1)
    Asistencia.objects.filter(pk=asistencia.pk).update(actualizado_en=pasado)
    asistencia.refresh_from_db()

    asistencia.estado = "TARDE"
    asistencia.save()

    asistencia.refresh_from_db()
    assert asistencia.actualizado_en > pasado
