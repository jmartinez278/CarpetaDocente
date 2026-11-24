"""Datos ficticios de las pruebas de direccion: reutiliza los de notas e institucion (DoD 8)."""

import datetime

import pytest

from asistencia.models import Asistencia, Jornada
from asistencia.servicios import dias_de_clase
from institucion.models import Estudiante, Seccion
from notas.tests.conftest import *  # noqa: F403 - fixtures compartidas
from repositorio.tests.conftest import (  # noqa: F401 - fixtures compartidas
    comunicacion,
    crear_sesion,
    material_de_referencia,
)

# Hoy es el lunes 22 de noviembre de 2027, en el IV bimestre (del 8 de noviembre al 18 de
# diciembre, el de ``bimestres``): 10 días de clase hasta ayer.
HOY = datetime.date(2027, 11, 22)
LETRAS = "ABCD"


def crear_seccion(anio, grado, nombre, docente=None, estudiantes=0):
    """Una sección ficticia con ``estudiantes`` activos."""
    seccion = Seccion.objects.create(anio_escolar=anio, grado=grado, nombre=nombre, docente=docente)
    Estudiante.objects.bulk_create(
        Estudiante(seccion=seccion, apellidos=f"APELLIDO {n:02}", nombres="NOMBRE")
        for n in range(estudiantes)
    )
    return seccion


def completar_asistencia(seccion, periodo, hasta, usuario, estado=Asistencia.Estado.ASISTIO):
    """Una jornada completa por cada día de clase del periodo hasta ``hasta``."""
    estudiantes = list(seccion.estudiantes.filter(estado=Estudiante.Estado.ACTIVO))
    jornadas = Jornada.objects.bulk_create(
        Jornada(seccion=seccion, fecha=dia, registrado_por=usuario)
        for dia in dias_de_clase(periodo, hasta)
    )
    Asistencia.objects.bulk_create(
        Asistencia(jornada=jornada, estudiante=estudiante, estado=estado)
        for jornada in jornadas
        for estudiante in estudiantes
    )


@pytest.fixture
def veinticuatro(anio_abierto, docente, bimestres):
    """Las 24 secciones del boceto: 4.º C sin docente, 6.º D sin estudiantes, 9 al día.

    Las al día tienen la asistencia completa hasta ayer y ninguna competencia marcada; las
    otras 13 no tienen jornadas. Todas con la misma docente ficticia.
    """
    ayer = HOY - datetime.timedelta(days=1)
    secciones = []
    for grado in range(1, 7):
        for nombre in LETRAS:
            sin_docente = (grado, nombre) == (4, "C")
            vacia = (grado, nombre) == (6, "D")
            seccion = crear_seccion(
                anio_abierto,
                grado,
                nombre,
                docente=None if sin_docente else docente,
                estudiantes=0 if vacia else 2,
            )
            secciones.append(seccion)
    con_trabajo = [s for s in secciones if (s.grado, s.nombre) not in {(4, "C"), (6, "D")}]
    for seccion in con_trabajo[:9]:
        completar_asistencia(seccion, bimestres[3], ayer, docente)
    return secciones
