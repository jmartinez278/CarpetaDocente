"""RegistroActividad: catálogo cerrado en la base, usuario vacío y solo lectura (D1, D3, D8)."""

import datetime

import pytest
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction

from actividad.models import CUENTAN_KPI_01, RESERVADAS, Operacion, RegistroActividad

pytestmark = pytest.mark.django_db


def _entrada(**campos):
    campos.setdefault("operacion", Operacion.INICIO_SESION)
    return RegistroActividad.objects.create(**campos)


def test_operacion_fuera_del_catalogo_la_rechaza_la_base():
    with pytest.raises(IntegrityError, match="ck_actividad_operacion"), transaction.atomic():
        _entrada(operacion="OPERACION_INVENTADA")
    assert RegistroActividad.objects.count() == 0


def test_usuario_vacio_se_permite():
    entrada = _entrada()
    entrada.refresh_from_db()
    assert entrada.usuario is None


def test_borrar_el_usuario_deja_la_entrada_con_usuario_vacio(docente):
    entrada = _entrada(usuario=docente)
    docente.delete()
    entrada.refresh_from_db()
    assert entrada.usuario is None


def test_guardar_de_nuevo_una_entrada_existente_lanza_permission_denied():
    entrada = _entrada(entidad="jornada")
    entrada.entidad = "otra"
    with pytest.raises(PermissionDenied):
        entrada.save()
    entrada.refresh_from_db()
    assert entrada.entidad == "jornada"


def test_borrar_una_entrada_lanza_permission_denied():
    entrada = _entrada()
    with pytest.raises(PermissionDenied):
        entrada.delete()
    assert RegistroActividad.objects.filter(pk=entrada.pk).exists()


def test_orden_de_la_mas_reciente_a_la_mas_antigua():
    zona = datetime.UTC
    vieja = _entrada(fecha_hora=datetime.datetime(2026, 10, 1, 8, 0, tzinfo=zona))
    nueva = _entrada(fecha_hora=datetime.datetime(2026, 10, 2, 8, 0, tzinfo=zona))
    mismo_instante = _entrada(fecha_hora=nueva.fecha_hora)
    assert list(RegistroActividad.objects.all()) == [mismo_instante, nueva, vieja]


def test_entidad_y_detalle_tienen_valores_por_defecto():
    entrada = _entrada()
    assert (entrada.entidad, entrada.entidad_id, entrada.detalle) == ("", "", {})


def test_solo_las_operaciones_de_asistencia_cuentan_para_kpi_01():
    assert CUENTAN_KPI_01 == {
        Operacion.REGISTRO_ASISTENCIA,
        Operacion.ASISTENCIA_CAMBIADA,
        Operacion.JORNADA_COMPLETA,
    }


def test_solo_intento_sin_permiso_esta_reservada():
    assert RESERVADAS == {Operacion.INTENTO_SIN_PERMISO}
