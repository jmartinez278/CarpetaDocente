"""``registrar``: única puerta de escritura al registro, dentro de la transacción (D2, D7)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from actividad import servicios
from actividad.models import Operacion, RegistroActividad
from actividad.servicios import DETALLE_PERMITIDO, registrar
from institucion.models import Institucion

pytestmark = pytest.mark.django_db


def test_guarda_usuario_operacion_entidad_id_como_texto_y_detalle(docente):
    registrar(
        docente,
        Operacion.REGISTRO_ASISTENCIA,
        entidad="jornada",
        entidad_id=42,
        detalle={"seccion": 7, "fecha": "2026-10-28"},
    )

    entrada = RegistroActividad.objects.get()
    assert entrada.usuario == docente
    assert entrada.operacion == Operacion.REGISTRO_ASISTENCIA
    assert entrada.entidad == "jornada"
    assert entrada.entidad_id == "42"
    assert entrada.detalle == {"seccion": 7, "fecha": "2026-10-28"}


def test_acepta_el_objeto_afectado_en_lugar_de_su_id(docente, institucion):
    registrar(docente, Operacion.INSTITUCION_EDITADA, "institucion", institucion)

    assert RegistroActividad.objects.get().entidad_id == str(institucion.pk)


def test_sin_entidad_ni_detalle_quedan_vacios(docente):
    registrar(docente, Operacion.INICIO_SESION)

    entrada = RegistroActividad.objects.get()
    assert (entrada.entidad, entrada.entidad_id, entrada.detalle) == ("", "", {})


def test_usuario_anonimo_queda_vacio():
    registrar(AnonymousUser(), Operacion.INICIO_SESION)

    assert RegistroActividad.objects.get().usuario is None


def test_usuario_none_de_un_comando_de_consola_queda_vacio():
    registrar(None, Operacion.DEMO_CARGADA)

    assert RegistroActividad.objects.get().usuario is None


def test_fuera_de_una_transaccion_lanza_runtime_error(docente, monkeypatch):
    # La fixture ``db`` envuelve cada prueba en una transacción; una real vaciaría la base y
    # rompería las pruebas con ``serialized_rollback`` de institucion.
    monkeypatch.setattr(servicios.connection, "in_atomic_block", False)
    with pytest.raises(RuntimeError):
        registrar(docente, Operacion.INICIO_SESION)

    assert RegistroActividad.objects.count() == 0


def test_operacion_fuera_del_catalogo_lanza_value_error_sin_guardar(docente):
    with pytest.raises(ValueError, match="operación"):
        registrar(docente, "OPERACION_INVENTADA")

    assert RegistroActividad.objects.count() == 0


def test_clave_de_detalle_no_permitida_lanza_value_error_sin_guardar(docente):
    with pytest.raises(ValueError, match="nombres"):
        registrar(docente, Operacion.ESTUDIANTE_EDITADO, detalle={"nombres": "ANA"})

    assert RegistroActividad.objects.count() == 0


def test_las_listas_de_detalle_son_de_operaciones_del_catalogo():
    assert set(DETALLE_PERMITIDO) <= set(Operacion)
    assert all(isinstance(claves, frozenset) for claves in DETALLE_PERMITIDO.values())


# Un savepoint se deshace igual que la transacción de la operación.
def test_la_operacion_falla_y_no_queda_entrada(docente):
    with pytest.raises(ZeroDivisionError), transaction.atomic():
        registrar(docente, Operacion.INSTITUCION_CREADA)
        1 / 0  # noqa: B018 - la operación de la misma transacción falla

    assert RegistroActividad.objects.count() == 0


def test_el_registro_falla_y_la_operacion_no_se_guarda(docente):
    def crear_y_registrar():
        with transaction.atomic():
            Institucion.objects.create(nombre="I.E. Ficticia N.° 9")
            registrar(docente, "OPERACION_INVENTADA")

    with pytest.raises(ValueError):
        crear_y_registrar()

    assert not Institucion.objects.filter(nombre="I.E. Ficticia N.° 9").exists()
