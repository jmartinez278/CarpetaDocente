"""Pruebas de Estudiante (spec estudiantes-seccion; design de US-006, D1; documento 11, 3.2)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from institucion import servicios
from institucion.models import Estudiante, Seccion

pytestmark = pytest.mark.django_db

MENSAJE_HOMONIMO = "Este estudiante ya está en la lista"


# --- normalizar_nombre ---


def test_normalizar_quita_espacios_de_mas():
    assert servicios.normalizar_nombre("  quispe   mamani ") == "QUISPE MAMANI"


def test_normalizar_quita_el_espacio_duro_de_excel():
    assert servicios.normalizar_nombre("quispe mamani ") == "QUISPE MAMANI"


def test_normalizar_conserva_tildes_y_enie():
    assert servicios.normalizar_nombre("ana lucía ñaupa") == "ANA LUCÍA ÑAUPA"


def test_normalizar_junta_las_tildes_descompuestas():
    descompuesto = "josé ñaupa"

    assert servicios.normalizar_nombre(descompuesto) == "JOSÉ ÑAUPA"
    assert servicios.normalizar_nombre(descompuesto) == servicios.normalizar_nombre("josé ñaupa")


# --- guardado ---


def test_save_guarda_la_forma_normalizada(seccion):
    estudiante = Estudiante.objects.create(
        seccion=seccion, apellidos="  quispe   mamani ", nombres="ana lucía"
    )

    estudiante.refresh_from_db()
    assert (estudiante.apellidos, estudiante.nombres) == ("QUISPE MAMANI", "ANA LUCÍA")


def test_el_estudiante_se_muestra_con_apellidos_y_nombres(seccion):
    estudiante = Estudiante.objects.create(seccion=seccion, apellidos="quispe", nombres="ana")

    assert str(estudiante) == "QUISPE, ANA"


# --- homónimos ---


def test_homonimo_exacto_lo_rechaza_la_base_de_datos(seccion):
    Estudiante.objects.create(seccion=seccion, apellidos="QUISPE MAMANI", nombres="ANA")

    with pytest.raises(IntegrityError), transaction.atomic():
        Estudiante.objects.create(seccion=seccion, apellidos="quispe  mamani", nombres="ana")


def test_homonimo_exacto_no_pasa_la_validacion(seccion):
    Estudiante.objects.create(seccion=seccion, apellidos="QUISPE MAMANI", nombres="ANA")
    nuevo = Estudiante(seccion=seccion, apellidos="quispe mamani", nombres="ana")

    with pytest.raises(ValidationError) as error:
        nuevo.full_clean()

    assert MENSAJE_HOMONIMO in error.value.messages


def test_mismo_nombre_en_otra_seccion_se_guarda(seccion):
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")

    Estudiante.objects.create(seccion=seccion, apellidos="QUISPE MAMANI", nombres="ANA")
    Estudiante.objects.create(seccion=otra, apellidos="QUISPE MAMANI", nombres="ANA")

    assert Estudiante.objects.count() == 2


# --- cascada desde la sección ---


def test_borrar_la_seccion_borra_a_sus_estudiantes(seccion):
    Estudiante.objects.create(seccion=seccion, apellidos="QUISPE", nombres="ANA")

    seccion.delete()

    assert Estudiante.objects.count() == 0
