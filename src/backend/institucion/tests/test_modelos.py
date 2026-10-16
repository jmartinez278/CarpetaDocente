"""Pruebas de la entidad Institución (spec cuentas-usuarios; documento 11, sección 3.1)."""

import pytest
from django.db import IntegrityError, transaction

from institucion.models import Institucion

pytestmark = pytest.mark.django_db


def test_institucion_valida_solo_con_nombre():
    institucion = Institucion.objects.create(nombre="I.E. Ficticia N.° 1")

    institucion.refresh_from_db()
    assert institucion.creado_en is not None
    assert institucion.codigo_modular is None
    assert institucion.organizacion_periodos is None


def test_codigo_modular_repetido_se_rechaza():
    Institucion.objects.create(nombre="I.E. Ficticia N.° 1", codigo_modular="0000001")

    with pytest.raises(IntegrityError), transaction.atomic():
        Institucion.objects.create(nombre="I.E. Ficticia N.° 2", codigo_modular="0000001")


def test_varias_instituciones_sin_codigo_modular_se_aceptan():
    Institucion.objects.create(nombre="I.E. Ficticia N.° 1")
    Institucion.objects.create(nombre="I.E. Ficticia N.° 2")

    assert Institucion.objects.filter(codigo_modular__isnull=True).count() == 2


@pytest.mark.parametrize("organizacion", ["BIMESTRE", "TRIMESTRE"])
def test_organizacion_de_periodos_permitida(organizacion):
    institucion = Institucion.objects.create(
        nombre="I.E. Ficticia N.° 1", organizacion_periodos=organizacion
    )

    assert institucion.organizacion_periodos == organizacion


def test_organizacion_de_periodos_no_permitida_se_rechaza():
    with pytest.raises(IntegrityError), transaction.atomic():
        Institucion.objects.create(nombre="I.E. Ficticia N.° 1", organizacion_periodos="SEMESTRE")
