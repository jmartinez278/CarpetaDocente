"""``registrar``: única puerta de escritura al registro, dentro de la transacción (D2, D7)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from actividad import servicios
from actividad.models import Operacion, RegistroActividad
from actividad.servicios import DETALLE_PERMITIDO, registrar
from institucion.models import Institucion

pytestmark = pytest.mark.django_db

# UUID de una sesión ficticia: la entidad de las operaciones sobre sesiones.
ID_SESION = "7d1c4a52-6c0e-4b7e-9d3a-2f5b8e1a9c04"
SOBRE_SESIONES = [
    "SESION_VISTA",
    "SESION_DESCARGADA",
    "SESION_COMPARTIDA",
    "SESION_DESCOMPARTIDA",
    "SESION_ELIMINADA",
]


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


def test_eliminar_una_sesion_solo_admite_si_estaba_compartida(docente):
    registrar(docente, "SESION_ELIMINADA", "sesion", ID_SESION, {"compartida": True})

    entrada = RegistroActividad.objects.get()
    assert (entrada.entidad, entrada.entidad_id) == ("sesion", ID_SESION)
    assert entrada.detalle == {"compartida": True}


def test_descargar_una_sesion_admite_el_modo_y_si_es_propia(docente):
    detalle = {"modo": "ver", "propia": False}

    registrar(docente, "SESION_DESCARGADA", "sesion", ID_SESION, detalle)

    assert RegistroActividad.objects.get().detalle == detalle


@pytest.mark.parametrize("operacion", SOBRE_SESIONES)
@pytest.mark.parametrize("clave", ["titulo", "proposito", "texto", "archivo_nombre"])
def test_ninguna_operacion_sobre_sesiones_admite_datos_de_la_sesion(docente, operacion, clave):
    # RN-015: el título, el propósito, el texto y el nombre del archivo nunca van al registro.
    with pytest.raises(ValueError, match=clave):
        registrar(docente, operacion, "sesion", ID_SESION, {clave: "Leemos un cuento"})

    assert RegistroActividad.objects.count() == 0


SOBRE_REFERENCIAS = [
    "SESION_REFERENCIA_CARGADA",
    "SESION_REFERENCIA_EDITADA",
    "SESION_REFERENCIA_ELIMINADA",
]


def test_editar_material_de_referencia_admite_los_nombres_de_los_campos(administrador):
    # Spec material-referencia, «Registro de la carga», escenario «Editar» (US-018, D7).
    detalle = {"campos": ["titulo", "fuente"]}

    registrar(administrador, "SESION_REFERENCIA_EDITADA", "sesion", ID_SESION, detalle)

    assert RegistroActividad.objects.get().detalle == detalle


@pytest.mark.parametrize("operacion", SOBRE_REFERENCIAS)
@pytest.mark.parametrize("clave", ["titulo", "fuente", "permiso_uso", "archivo_nombre"])
def test_ninguna_operacion_de_referencia_admite_datos_de_la_sesion(administrador, operacion, clave):
    # RN-015: ni el título, ni la fuente, ni el permiso de uso, ni el nombre del archivo.
    with pytest.raises(ValueError, match=clave):
        registrar(administrador, operacion, "sesion", ID_SESION, {clave: "Equipo del proyecto"})

    assert RegistroActividad.objects.count() == 0


@pytest.mark.parametrize("operacion", ["SESION_REFERENCIA_CARGADA", "SESION_REFERENCIA_ELIMINADA"])
def test_cargar_y_eliminar_material_de_referencia_no_admiten_detalle(administrador, operacion):
    with pytest.raises(ValueError, match="campos"):
        registrar(administrador, operacion, "sesion", ID_SESION, {"campos": ["titulo"]})


@pytest.mark.parametrize("operacion", ["SESION_VISTA", "SESION_COMPARTIDA", "SESION_DESCOMPARTIDA"])
def test_ver_compartir_y_dejar_de_compartir_no_admiten_detalle(docente, operacion):
    with pytest.raises(ValueError, match="compartida"):
        registrar(docente, operacion, "sesion", ID_SESION, {"compartida": True})

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
