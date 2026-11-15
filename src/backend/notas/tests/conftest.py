"""Datos ficticios de las pruebas de notas: reutiliza los de institucion (DoD 8)."""

import datetime

import pytest
from django.utils import timezone

from catalogo.models import Competencia, InstitucionArea
from institucion.models import Estudiante, Institucion, Periodo
from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas
from notas.models import Calificacion, CompetenciaPeriodo

# Códigos SIAGIE de las áreas que usan las pruebas (catalogo/0002).
MATEMATICA = "063"
COMUNICACION = "0005"
ARTE = "0001"
CASTELLANO = "0002"
INGLES = "0003"
EDUCACION_FISICA = "031"

# Fechas del spec competencias-periodo: el bimestre 3 va del 10 de agosto al 30 de octubre.
BIMESTRES = [
    (datetime.date(2027, 3, 9), datetime.date(2027, 5, 15)),
    (datetime.date(2027, 5, 25), datetime.date(2027, 7, 24)),
    (datetime.date(2027, 8, 10), datetime.date(2027, 10, 30)),
    (datetime.date(2027, 11, 8), datetime.date(2027, 12, 18)),
]
OCT_30 = datetime.date(2027, 10, 30)
AGO_1 = datetime.date(2027, 8, 1)
MAR_2 = datetime.date(2027, 3, 2)
NOV_20 = datetime.date(2027, 11, 20)


def ids_de(*codigos):
    """Los id de las competencias activas de esas áreas."""
    return set(
        Competencia.objects.filter(area__codigo_siagie__in=codigos, activa=True).values_list(
            "pk", flat=True
        )
    )


def competencia(codigo, orden):
    """La competencia ``orden`` (1…n) del área ``codigo``."""
    return Competencia.objects.get(area__codigo_siagie=codigo, orden=orden)


# Una conclusión ficticia válida (de 10 a 500 caracteres), sin nombres.
CONCLUSION = "Necesita apoyo para explicar sus procedimientos."


def crear_estudiantes(seccion, *nombres, estado=Estudiante.Estado.ACTIVO):
    """Estudiantes ficticios de ``seccion``; cada nombre es «APELLIDOS, NOMBRES»."""
    creados = []
    for completo in nombres:
        apellidos, nombres_ = (parte.strip() for parte in completo.split(","))
        creados.append(
            Estudiante.objects.create(
                seccion=seccion, apellidos=apellidos, nombres=nombres_, estado=estado
            )
        )
    return creados


def poner_nota(estudiante, competencia_id, periodo, nivel="A", conclusion=None):
    """Guarda una nota directo en la base; en B y C, con ``CONCLUSION`` si no se da otra."""
    if conclusion is None:
        conclusion = CONCLUSION if nivel in ("B", "C") else ""
    return Calificacion.objects.create(
        estudiante=estudiante,
        competencia_id=getattr(competencia_id, "pk", competencia_id),
        periodo=periodo,
        nivel=nivel,
        conclusion_descriptiva=conclusion,
    )


def con_notas(seccion, periodo, ids, nivel="A"):
    """Una nota en cada competencia ``ids`` del periodo, de un estudiante ficticio de la sección.

    Usa el primer estudiante de la sección o crea uno.
    """
    estudiante = seccion.estudiantes.order_by("pk").first()
    if estudiante is None:
        (estudiante,) = crear_estudiantes(seccion, "PAREDES, NOA")
    for competencia_id in ids:
        poner_nota(estudiante, competencia_id, periodo, nivel)
    return estudiante


def marcar(seccion, periodo, ids):
    """Marca ``ids`` en el periodo directo en la base, sin entrada de actividad."""
    CompetenciaPeriodo.objects.bulk_create(
        CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=i) for i in ids
    )


@pytest.fixture
def bimestre_1(anio_abierto):
    return Periodo.objects.create(
        anio_escolar=anio_abierto,
        numero=1,
        fecha_inicio=datetime.date(2027, 3, 16),
        fecha_fin=datetime.date(2027, 5, 15),
    )


@pytest.fixture
def seccion_tutora(seccion, docente):
    """2.º A con su tutora."""
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def areas_a_cargo(institucion):
    """Educación Física e Inglés a cargo del docente de curso, como en la I.E. (decisión 12)."""
    InstitucionArea.objects.filter(
        institucion=institucion, area__codigo_siagie__in=[EDUCACION_FISICA, INGLES]
    ).update(a_cargo_docente_curso=True)


@pytest.fixture
def bimestres(institucion, anio_abierto):
    """Los 4 bimestres del spec, en una institución organizada en bimestres."""
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    return [
        Periodo.objects.create(
            anio_escolar=anio_abierto, numero=numero, fecha_inicio=inicio, fecha_fin=fin
        )
        for numero, (inicio, fin) in enumerate(BIMESTRES, start=1)
    ]


@pytest.fixture
def universo_ie(areas_a_cargo):
    """Las 21 competencias que marca la tutora en la I.E. (sin Castellano, Inglés ni E. F.)."""
    return set(
        Competencia.objects.filter(activa=True)
        .exclude(area__codigo_siagie__in=[CASTELLANO, INGLES, EDUCACION_FISICA])
        .values_list("pk", flat=True)
    )


@pytest.fixture
def hoy(monkeypatch):
    """Hoy es el 30 de octubre en Lima, sin tocar el reloj; ``hoy["valor"]`` lo cambia."""
    dia = {"valor": OCT_30}
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: dia["valor"])
    return dia


@pytest.fixture
def cliente(client, docente, seccion_tutora):
    client.force_login(docente)
    return client


@pytest.fixture
def ie(seccion_tutora, bimestres, universo_ie):
    """La I.E. del spec: 4 bimestres y Educación Física e Inglés a cargo del docente de curso."""
    return universo_ie


# --- Hoja de notas en el navegador (test_hoja_e2e y test_borradores_e2e) ---


@pytest.fixture
def estudiantes(seccion_tutora):
    """Ana Quispe y Luis Rojas, activos y ficticios."""
    return crear_estudiantes(seccion_tutora, "QUISPE, ANA", "ROJAS, LUIS")


@pytest.fixture
def hoja_lista(seccion_tutora, ie, bimestres, estudiantes):
    """Matemática y Comunicación marcadas en B2 y B3 (4 y 3 competencias activas)."""
    for periodo in bimestres[1:3]:
        marcar(seccion_tutora, periodo, ids_de(MATEMATICA, COMUNICACION))
    return bimestres[2]


@pytest.fixture
def abrir_hoja(live_server, page, docente, clave, seccion_tutora, monkeypatch, hoja_lista):
    """Abre la hoja de la tutora el día pedido (el 30 de octubre por defecto)."""
    from playwright.sync_api import expect

    from cuentas.tests.e2e import con_pantalla, fijar_hora_de_lima, ingresar
    from notas.tests.e2e import LIMA, url_hoja

    def abrir(ancho=1280, tema="light", dia=OCT_30, **parametros):
        fijar_hora_de_lima(
            monkeypatch, datetime.datetime(dia.year, dia.month, dia.day, 9, 0, tzinfo=LIMA)
        )
        con_pantalla(page, ancho, tema)
        ingresar(page, live_server, docente, clave)
        page.wait_for_url(f"{live_server.url}/docente/")
        page.goto(url_hoja(live_server, seccion_tutora, **{"area": MATEMATICA, **parametros}))
        expect(page.get_by_role("grid")).to_be_visible()
        return page

    return abrir
