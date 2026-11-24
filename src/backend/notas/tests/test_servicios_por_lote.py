"""Notas por lote para la dirección (US-040, D3): las mismas reglas que la hoja, sin consultar por
sección ni por área."""

import pytest

from catalogo.models import Competencia, InstitucionArea
from institucion.models import Estudiante, Seccion
from notas import servicios
from notas.tests.conftest import (
    COMUNICACION,
    INGLES,
    MATEMATICA,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def con_faltantes(seccion_tutora, ie, bimestres):
    """2.º A en el III bimestre: Matemática y Comunicación e Inglés marcadas, con notas sueltas.

    Tres activos y un trasladado sin notas; Matemática C4 inactiva después de marcarla.
    """
    periodo = bimestres[2]
    activos = crear_estudiantes(seccion_tutora, "ROJAS, MATEO", "ÁLVAREZ, LUCÍA", "CCAHUANA, PEDRO")
    crear_estudiantes(seccion_tutora, "TORRES, IVÁN", estado=Estudiante.Estado.TRASLADADO)
    marcar(seccion_tutora, periodo, ids_de(MATEMATICA, COMUNICACION) | ids_de(INGLES))
    Competencia.objects.filter(pk=competencia(MATEMATICA, 4).pk).update(activa=False)
    poner_nota(activos[0], competencia(MATEMATICA, 1), periodo, "AD")
    poner_nota(activos[1], competencia(MATEMATICA, 1), periodo, "B")
    poner_nota(activos[1], competencia(COMUNICACION, 2), periodo, "C")
    poner_nota(activos[2], competencia(COMUNICACION, 1), periodo, "A")
    return periodo, activos


def faltantes_de_la_hoja(seccion, periodo):
    """La suma de ``notas_faltantes`` de la tutora en cada área de la institución."""
    filas = InstitucionArea.objects.filter(institucion_id=seccion.anio_escolar.institucion_id)
    return sum(
        len(servicios.notas_faltantes(seccion.docente, seccion, periodo, fila)) for fila in filas
    )


def test_faltantes_por_seccion_da_lo_mismo_que_la_hoja(seccion_tutora, con_faltantes):
    """Zona de cuidado (D3): la versión por lote no se separa de la regla de la hoja."""
    periodo, _ = con_faltantes

    conteo = servicios.faltantes_por_seccion([seccion_tutora], periodo)[seccion_tutora.pk]

    # Matemática: 3 activas × 3 activos − 2 notas; Comunicación: 3 × 3 − 2; Inglés no cuenta.
    assert conteo.faltan == faltantes_de_la_hoja(seccion_tutora, periodo) == 14


def test_el_total_son_las_celdas_de_la_hoja(seccion_tutora, con_faltantes):
    """«N de M registradas»: M son las celdas de los activos en las competencias marcadas."""
    periodo, _ = con_faltantes

    conteo = servicios.faltantes_por_seccion([seccion_tutora], periodo)[seccion_tutora.pk]

    assert conteo.total == 18
    assert conteo.registradas == 4


def test_sin_docente_no_falta_ninguna(seccion, ie, bimestres):
    sin_docente = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=4, nombre="C")
    crear_estudiantes(sin_docente, "QUISPE, ANA")
    marcar(sin_docente, bimestres[2], ids_de(MATEMATICA))

    conteo = servicios.faltantes_por_seccion([sin_docente], bimestres[2])[sin_docente.pk]

    assert (conteo.faltan, conteo.total) == (0, 0)


def test_cada_seccion_cuenta_las_suyas_en_una_consulta(
    seccion_tutora, con_faltantes, otra_docente, django_assert_num_queries
):
    periodo, _ = con_faltantes
    otra = Seccion.objects.create(
        anio_escolar=seccion_tutora.anio_escolar, grado=2, nombre="B", docente=otra_docente
    )
    crear_estudiantes(otra, "QUISPE, ANA", "MAMANI, LUIS")
    marcar(otra, periodo, [competencia(MATEMATICA, 1).pk])
    sin_nada = Seccion.objects.create(anio_escolar=seccion_tutora.anio_escolar, grado=3, nombre="A")

    with django_assert_num_queries(1):
        conteos = servicios.faltantes_por_seccion([seccion_tutora, otra, sin_nada], periodo)

    assert conteos[seccion_tutora.pk].faltan == 14
    assert (conteos[otra.pk].faltan, conteos[otra.pk].total) == (2, 2)
    assert conteos[otra.pk].faltan == faltantes_de_la_hoja(otra, periodo)
    assert (conteos[sin_nada.pk].faltan, conteos[sin_nada.pk].total) == (0, 0)


def test_niveles_por_area(seccion_tutora, con_faltantes):
    """La tabla por área de la pestaña Notas: AD, A, B, C y las que faltan suman el total."""
    periodo, activos = con_faltantes
    # Una nota del trasladado y una de la competencia inactiva no entran.
    trasladado = seccion_tutora.estudiantes.get(estado=Estudiante.Estado.TRASLADADO)
    poner_nota(trasladado, competencia(MATEMATICA, 2), periodo, "A")
    poner_nota(activos[0], competencia(MATEMATICA, 4), periodo, "A")

    niveles = servicios.niveles_por_area(seccion_tutora, periodo)

    matematica = competencia(MATEMATICA, 1).area_id
    comunicacion = competencia(COMUNICACION, 1).area_id
    assert niveles[matematica] == {"AD": 1, "A": 0, "B": 1, "C": 0}
    assert niveles[comunicacion] == {"AD": 0, "A": 1, "B": 0, "C": 1}
    assert competencia(INGLES, 1).area_id not in niveles
