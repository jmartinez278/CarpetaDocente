"""Verificación de acceso a una sección y registro del intento (spec acceso-secciones; US-004).

D1 y D4: ``seccion_de_la_docente`` decide el motivo en una sola consulta. D5:
``registrar_intento_sin_permiso`` deja una entrada INTENTO_SIN_PERMISO por llamada.
"""

import pytest

from actividad.models import Operacion, RegistroActividad
from institucion import servicios
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.django_db


@pytest.fixture
def seccion_docente(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def anio_cerrado(institucion):
    return AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )


def _motivo(usuario, seccion_id, estudiante_id=None):
    with pytest.raises(servicios.SinPermiso) as error:
        servicios.seccion_de_la_docente(usuario, seccion_id, estudiante_id)
    return error.value.motivo


# --- seccion_de_la_docente (D1, D4) ---


def test_acceso_devuelve_la_seccion_de_la_docente_sin_estudiante(docente, seccion_docente):
    assert servicios.seccion_de_la_docente(docente, seccion_docente.pk) == (seccion_docente, None)


def test_acceso_devuelve_la_seccion_y_su_estudiante(docente, seccion_docente):
    estudiante = Estudiante.objects.create(
        seccion=seccion_docente, apellidos="QUISPE", nombres="ANA"
    )

    assert servicios.seccion_de_la_docente(docente, seccion_docente.pk, estudiante.pk) == (
        seccion_docente,
        estudiante,
    )


def test_acceso_seccion_inexistente_es_inexistente(docente, seccion_docente):
    assert _motivo(docente, seccion_docente.pk + 1000) == servicios.INEXISTENTE == "inexistente"


def test_acceso_seccion_de_otra_docente_es_ajena(otra_docente, seccion_docente):
    assert _motivo(otra_docente, seccion_docente.pk) == servicios.AJENA == "ajena"


def test_acceso_seccion_de_otra_docente_en_anio_cerrado_es_ajena(
    otra_docente, docente, anio_cerrado
):
    cerrada = Seccion.objects.create(
        anio_escolar=anio_cerrado, grado=3, nombre="B", docente=docente
    )

    assert _motivo(otra_docente, cerrada.pk) == servicios.AJENA


def test_acceso_seccion_propia_en_anio_cerrado_es_anio_cerrado(docente, anio_cerrado):
    cerrada = Seccion.objects.create(
        anio_escolar=anio_cerrado, grado=3, nombre="B", docente=docente
    )

    assert _motivo(docente, cerrada.pk) == servicios.ANIO_CERRADO_ACCESO == "anio_cerrado"


def test_acceso_seccion_sin_docente_es_ajena(docente, seccion):
    assert _motivo(docente, seccion.pk) == servicios.AJENA


def test_acceso_estudiante_de_otra_seccion_es_estudiante(docente, seccion_docente, anio_abierto):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=4, nombre="B")
    ajeno = Estudiante.objects.create(seccion=otra, apellidos="MAMANI", nombres="ROSA")

    assert _motivo(docente, seccion_docente.pk, ajeno.pk) == servicios.ESTUDIANTE == "estudiante"


def test_acceso_estudiante_inexistente_es_estudiante(docente, seccion_docente):
    assert _motivo(docente, seccion_docente.pk, 999_999) == servicios.ESTUDIANTE


def test_acceso_la_seccion_ajena_manda_sobre_el_estudiante(otra_docente, seccion_docente):
    """D4: el orden del motivo; con la sección ajena no importa el estudiante."""
    assert _motivo(otra_docente, seccion_docente.pk, 999_999) == servicios.AJENA


def test_acceso_lo_decide_en_una_consulta_por_objeto(
    docente, seccion_docente, django_assert_num_queries
):
    estudiante = Estudiante.objects.create(
        seccion=seccion_docente, apellidos="QUISPE", nombres="ANA"
    )

    with django_assert_num_queries(2):
        servicios.seccion_de_la_docente(docente, seccion_docente.pk, estudiante.pk)


# --- registrar_intento_sin_permiso (D5) ---


def test_acceso_registrar_intento_deja_una_entrada_con_ruta_y_motivo(docente, seccion_docente):
    ruta = f"/docente/secciones/{seccion_docente.pk}/notas/"

    servicios.registrar_intento_sin_permiso(docente, seccion_docente.pk, ruta, servicios.AJENA)

    entrada = RegistroActividad.objects.get()
    assert entrada.operacion == Operacion.INTENTO_SIN_PERMISO
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(seccion_docente.pk))
    assert entrada.detalle == {"ruta": ruta, "motivo": "ajena"}


def test_acceso_cada_intento_cuenta(docente, seccion_docente):
    for _ in range(3):
        servicios.registrar_intento_sin_permiso(
            docente, seccion_docente.pk, "/docente/secciones/1/estudiantes/", servicios.AJENA
        )

    assert RegistroActividad.objects.filter(operacion=Operacion.INTENTO_SIN_PERMISO).count() == 3


def test_acceso_intento_con_una_clave_de_mas_lanza_value_error(docente, seccion_docente):
    from django.db import transaction

    from actividad.servicios import registrar

    with pytest.raises(ValueError, match="nombres"), transaction.atomic():
        registrar(
            docente,
            Operacion.INTENTO_SIN_PERMISO,
            entidad="seccion",
            entidad_id=seccion_docente.pk,
            detalle={"ruta": "/docente/", "motivo": "ajena", "nombres": "ANA"},
        )

    assert not RegistroActividad.objects.exists()
