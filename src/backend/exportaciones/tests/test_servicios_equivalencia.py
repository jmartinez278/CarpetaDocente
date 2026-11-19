"""Corregir la equivalencia: «¿No es esta sección?» (US-024/025, design D13).

Specs «Corregir la equivalencia» y, en registro-actividad, «Equivalencia de sección borrada».
"""

import pytest

from actividad.models import Operacion, RegistroActividad
from exportaciones import servicios
from exportaciones.models import EquivalenciaSeccion
from exportaciones.tests.plantilla import generar
from institucion.models import AnioEscolar, Seccion
from notas.tests.conftest import MATEMATICA, competencia, crear_estudiantes, poner_nota

pytestmark = pytest.mark.django_db


@pytest.fixture
def b_con_notas(secciones_de_segundo, ie_siagie, bimestres):
    """2.º B con una nota de Matemática en el bimestre 3."""
    b = secciones_de_segundo[1]
    (estudiante,) = crear_estudiantes(b, "QUISPE ROJAS, NOA")
    poner_nota(estudiante, competencia(MATEMATICA, 1), bimestres[2], "A")
    return b


def guardar(seccion, nombre="TRIUNFADORES"):
    return EquivalenciaSeccion.objects.create(
        seccion=seccion,
        anio_escolar=seccion.anio_escolar,
        grado=seccion.grado,
        codigo_siagie="01",
        nombre_siagie=nombre,
    )


def completar(usuario, seccion_id=None, **campos):
    campos.setdefault("hojas", {"063-MATE": 1})
    campos.setdefault("nombres", ["QUISPE ROJAS, NOA"])
    return servicios.completar_plantilla(usuario, generar(**campos), seccion_id)


def entradas():
    return RegistroActividad.objects.filter(operacion=Operacion.EQUIVALENCIA_SECCION_BORRADA)


def test_borrar_la_propia_deja_equivalencia_seccion_borrada(direccion, b_con_notas):
    equivalencia = guardar(b_con_notas)

    servicios.borrar_equivalencia(direccion, equivalencia.pk)

    assert not EquivalenciaSeccion.objects.exists()
    entrada = entradas().get()
    assert (entrada.usuario, entrada.entidad, entrada.entidad_id) == (
        direccion,
        "seccion",
        str(b_con_notas.pk),
    )
    assert entrada.detalle == {"anio": 2027, "grado": 2}


def test_la_siguiente_plantilla_vuelve_a_preguntar_con_esa_seccion(direccion, b_con_notas):
    resumen = completar(direccion, b_con_notas.pk)
    assert resumen.seccion == b_con_notas

    servicios.borrar_equivalencia(direccion, resumen.equivalencia_id)

    with pytest.raises(servicios.EligeSeccion) as error:
        completar(direccion)
    assert b_con_notas in error.value.opciones


def test_la_de_otra_institucion_no_se_borra(direccion, otra_institucion):
    otro_anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    ajena = guardar(Seccion.objects.create(anio_escolar=otro_anio, grado=2, nombre="B"))

    with pytest.raises(servicios.EquivalenciaInexistente) as error:
        servicios.borrar_equivalencia(direccion, ajena.pk)

    assert str(error.value) == "Esta equivalencia ya no existe."
    assert EquivalenciaSeccion.objects.filter(pk=ajena.pk).exists()
    assert not entradas().exists()


@pytest.mark.parametrize("equivalencia_id", [999_999, "x", None, 2**63, "9" * 30, -1])
def test_una_que_no_existe_no_deja_entrada(direccion, equivalencia_id):
    with pytest.raises(servicios.EquivalenciaInexistente):
        servicios.borrar_equivalencia(direccion, equivalencia_id)

    assert not entradas().exists()


def test_el_borrado_repetido_no_deja_otra_entrada(direccion, b_con_notas):
    equivalencia = guardar(b_con_notas)
    servicios.borrar_equivalencia(direccion, equivalencia.pk)

    with pytest.raises(servicios.EquivalenciaInexistente):
        servicios.borrar_equivalencia(direccion, equivalencia.pk)

    assert entradas().count() == 1


def test_sin_institucion_no_borra(administrador, b_con_notas):
    equivalencia = guardar(b_con_notas)

    with pytest.raises(servicios.EquivalenciaInexistente):
        servicios.borrar_equivalencia(administrador, equivalencia.pk)

    assert EquivalenciaSeccion.objects.exists()


# --- El resumen lleva la equivalencia solo si la sección salió de una (D13) ---


def test_por_equivalencia_guardada_el_resumen_lleva_su_id(direccion, b_con_notas):
    equivalencia = guardar(b_con_notas)

    assert completar(direccion).equivalencia_id == equivalencia.pk


def test_por_equivalencia_nueva_el_resumen_lleva_su_id(direccion, b_con_notas):
    resumen = completar(direccion, b_con_notas.pk)

    assert resumen.equivalencia_id == EquivalenciaSeccion.objects.get().pk


def test_por_nombre_el_resumen_no_lleva_equivalencia(direccion, b_con_notas):
    assert completar(direccion, nombre_seccion="b").equivalencia_id is None
