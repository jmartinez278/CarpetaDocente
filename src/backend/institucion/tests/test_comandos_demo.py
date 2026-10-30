"""Pruebas de los comandos de la demostración (spec datos-demostracion; EN-06, D6 a D9)."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from asistencia.models import Asistencia, Jornada
from cuentas.models import Usuario
from institucion import demo, servicios
from institucion.models import Estudiante, Seccion

pytestmark = pytest.mark.django_db


@pytest.fixture
def anio(institucion):
    """El año del calendario: el comando toma la asistencia de los días anteriores a hoy."""
    anio_escolar, _, _ = servicios.cargar_secciones(institucion, timezone.localdate().year)
    return anio_escolar


@pytest.fixture(autouse=True)
def demo_clave(monkeypatch, clave):
    monkeypatch.setenv("DEMO_CLAVE", clave)


def correr(comando, **opciones):
    salida = StringIO()
    call_command(comando, stdout=salida, **opciones)
    return salida.getvalue()


@pytest.fixture
def cargada(institucion, anio, clave):
    demo.cargar_demo(institucion, estudiantes=3, hoy=timezone.localdate(), clave=clave)


@pytest.fixture
def tres_a(anio, docente):
    sec = Seccion.objects.get(anio_escolar=anio, grado=3, nombre="A")
    sec.docente = docente
    sec.save()
    servicios.importar_lista(sec, "QUISPE MAMANI, ANA\nROJAS HUAMÁN, LUIS")
    jornada = Jornada.objects.create(
        seccion=sec, fecha=timezone.localdate(), registrado_por=docente
    )
    for estudiante in sec.estudiantes.all():
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")
    return sec


# --- cargar_demo ---


def test_cargar_demo_imprime_el_resumen(institucion, anio, settings):
    settings.DEBUG = True

    salida = correr("cargar_demo", institucion=institucion.pk, estudiantes=3)

    assert "Demostración cargada" in salida
    assert "1.º A" in salida and "2.º D" in salida
    assert "3 estudiantes por sección" in salida
    assert Estudiante.objects.count() == 24


def test_cargar_demo_con_confirmar_fuera_de_desarrollo(institucion, anio):
    correr("cargar_demo", institucion=institucion.pk, estudiantes=3, confirmar=True)

    assert Estudiante.objects.count() == 24


def test_cargar_demo_fuera_de_desarrollo_sin_confirmar(institucion, anio):
    salida = StringIO()

    with pytest.raises(CommandError, match="--confirmar"):
        call_command("cargar_demo", institucion=institucion.pk, stdout=salida)

    assert "1.º A" in salida.getvalue()
    assert not Estudiante.objects.exists()
    assert not Usuario.objects.filter(username__in=demo.CUENTAS_DEMO).exists()


def test_cargar_demo_sin_clave(institucion, anio, settings, monkeypatch):
    settings.DEBUG = True
    monkeypatch.delenv("DEMO_CLAVE")

    with pytest.raises(CommandError, match="DEMO_CLAVE"):
        correr("cargar_demo", institucion=institucion.pk)

    assert not Estudiante.objects.exists()


def test_cargar_demo_negada_es_error_del_comando(institucion, anio, settings, docente):
    settings.DEBUG = True
    dos_b = Seccion.objects.get(anio_escolar=anio, grado=2, nombre="B")
    dos_b.docente = docente
    dos_b.save()

    with pytest.raises(CommandError, match="2.º B"):
        correr("cargar_demo", institucion=institucion.pk)


def test_cargar_demo_institucion_inexistente(db):
    with pytest.raises(CommandError, match="No existe la institución 999"):
        correr("cargar_demo", institucion=999, confirmar=True)


# --- quitar_demo ---


def test_quitar_demo_sin_confirmar_dice_lo_que_borraria(cargada):
    with pytest.raises(CommandError) as error:
        correr("quitar_demo")

    assert "8 secciones" in str(error.value)
    assert "24 estudiantes" in str(error.value)
    assert Estudiante.objects.count() == 24


def test_quitar_demo_con_confirmar(cargada):
    salida = correr("quitar_demo", confirmar=True)

    assert "8 secciones demo liberadas" in salida
    assert not Estudiante.objects.exists()


def test_quitar_demo_sin_demo(db):
    salida = correr("quitar_demo", confirmar=True)

    assert "No hay demostración" in salida


# --- descartar_seccion ---


def test_descartar_sin_confirmar_dice_lo_que_borraria(tres_a):
    with pytest.raises(CommandError) as error:
        correr("descartar_seccion", seccion=tres_a.pk)

    assert "2 estudiantes, 1 jornadas y 2 estados" in str(error.value)
    assert tres_a.estudiantes.count() == 2


def test_descartar_con_confirmar(tres_a, docente):
    salida = correr("descartar_seccion", seccion=tres_a.pk, confirmar=True)

    assert "2 estudiantes, 1 jornadas y 2 estados" in salida
    tres_a.refresh_from_db()
    assert tres_a.docente == docente
    assert not tres_a.estudiantes.exists()


def test_descartar_seccion_inexistente(db):
    with pytest.raises(CommandError, match="No existe la sección 999"):
        correr("descartar_seccion", seccion=999, confirmar=True)
