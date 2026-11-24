"""Estado de las secciones, periodo elegido y resumen de la I.E. (US-040, D3 y D4; spec
consolidados-direccion)."""

import datetime
from decimal import Decimal

import pytest

from asistencia.models import Asistencia
from direccion import servicios
from direccion.tests.conftest import HOY, completar_asistencia, crear_seccion
from institucion.models import AnioEscolar, Estudiante, Periodo
from notas.servicios import ANTERIOR, VIGENTE
from notas.tests.conftest import MATEMATICA, competencia, ids_de, marcar, poner_nota

pytestmark = pytest.mark.django_db

AYER = HOY - datetime.timedelta(days=1)
LIMA = datetime.timezone(datetime.timedelta(hours=-5))


def en_lima(*partes):
    return datetime.datetime(*partes, tzinfo=LIMA)


# --- Periodos del año y periodo elegido (D4) ---


def elegido(institucion, hoy, pedido=None):
    periodos = servicios.periodos_del_anio(institucion, hoy)
    return servicios.periodo_de_la_consulta(periodos, pedido)


def test_los_periodos_son_los_del_anio_abierto_con_su_estado(institucion, bimestres):
    periodos = servicios.periodos_del_anio(institucion, HOY)

    assert [p.romano for p in periodos] == ["I", "II", "III", "IV"]
    assert [p.estado for p in periodos] == [ANTERIOR, ANTERIOR, ANTERIOR, VIGENTE]
    assert periodos[3].nombre_romano == "IV bimestre"


def test_sin_anio_abierto_no_hay_periodos(institucion, anio_abierto, bimestres):
    AnioEscolar.objects.filter(pk=anio_abierto.pk).update(estado=AnioEscolar.Estado.CERRADO)

    assert servicios.periodos_del_anio(institucion, HOY) == []


def test_no_entran_los_periodos_de_otra_institucion(institucion, otra_institucion, bimestres):
    otro_anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    Periodo.objects.create(
        anio_escolar=otro_anio,
        numero=1,
        fecha_inicio=datetime.date(2027, 3, 1),
        fecha_fin=datetime.date(2027, 12, 20),
    )

    assert len(servicios.periodos_del_anio(otra_institucion, HOY)) == 1
    assert len(servicios.periodos_del_anio(institucion, HOY)) == 4


def test_entra_en_el_vigente(institucion, bimestres):
    assert elegido(institucion, HOY).numero == 4


def test_un_periodo_anterior_pedido(institucion, bimestres):
    assert elegido(institucion, HOY, "2").numero == 2


def test_un_periodo_futuro_pedido_abre_el_vigente(institucion, bimestres):
    assert elegido(institucion, datetime.date(2027, 8, 20), "4").numero == 3


def test_un_pedido_que_no_vale_abre_el_vigente(institucion, bimestres):
    assert elegido(institucion, HOY, "9").numero == 4
    assert elegido(institucion, HOY, "x").numero == 4


def test_entre_periodos_abre_el_ultimo_pasado(institucion, bimestres):
    assert elegido(institucion, datetime.date(2027, 11, 1)).numero == 3


def test_antes_del_primero_no_hay_elegido(institucion, bimestres):
    assert elegido(institucion, datetime.date(2027, 3, 2)) is None
    assert elegido(institucion, datetime.date(2027, 3, 2), "1") is None


def test_sin_periodos_no_hay_elegido(institucion, anio_abierto):
    assert elegido(institucion, HOY) is None


# --- Estado de las secciones (D3) ---


@pytest.fixture
def cinco(anio_abierto, docente, otra_docente, bimestres, areas_a_cargo):
    """1.º A con 2 días sin completar, 1.º C sin docente, 2.º A con notas que faltan, 2.º B al
    día y 3.º A sin estudiantes, creadas en desorden."""
    periodo = bimestres[3]
    dos_b = crear_seccion(anio_abierto, 2, "B", otra_docente, estudiantes=2)
    tres_a = crear_seccion(anio_abierto, 3, "A", docente)
    dos_a = crear_seccion(anio_abierto, 2, "A", docente, estudiantes=3)
    uno_c = crear_seccion(anio_abierto, 1, "C", estudiantes=2)
    uno_a = crear_seccion(anio_abierto, 1, "A", otra_docente, estudiantes=1)
    for seccion in (dos_b, dos_a):
        completar_asistencia(seccion, periodo, AYER, docente)
    completar_asistencia(uno_a, periodo, datetime.date(2027, 11, 17), docente)
    marcar(dos_a, periodo, [competencia(MATEMATICA, 1).pk, competencia(MATEMATICA, 2).pk])
    poner_nota(dos_a.estudiantes.first(), competencia(MATEMATICA, 1), periodo, "A")
    # 2.º B: una marca con todas sus notas no la atrasa.
    marcar(dos_b, periodo, [competencia(MATEMATICA, 1).pk])
    for estudiante in dos_b.estudiantes.all():
        poner_nota(estudiante, competencia(MATEMATICA, 1), periodo, "AD")
    return uno_a, uno_c, dos_a, dos_b, tres_a


def test_los_cuatro_estados_en_orden_de_grado_y_nombre(institucion, bimestres, cinco):
    uno_a, uno_c, dos_a, dos_b, tres_a = cinco

    estados = servicios.estado_de_las_secciones(institucion, bimestres[3], HOY)

    assert [e.seccion for e in estados] == [uno_a, uno_c, dos_a, dos_b, tres_a]
    assert [e.estado for e in estados] == [
        servicios.ATRASADA,
        servicios.SIN_DOCENTE,
        servicios.ATRASADA,
        servicios.AL_DIA,
        servicios.SIN_ESTUDIANTES,
    ]
    de = {e.seccion: e for e in estados}
    assert (de[uno_a].notas_faltan, de[uno_a].dias_sin_completar) == (0, 2)
    assert (de[dos_a].notas_faltan, de[dos_a].notas_total, de[dos_a].dias_sin_completar) == (
        5,
        6,
        0,
    )
    assert (de[dos_b].estudiantes, de[dos_b].tutora) == (2, dos_b.docente)


def test_sin_docente_manda_y_no_suma(institucion, anio_abierto, docente, bimestres):
    """Sin docente y sin estudiantes es «Sin docente»; ninguna de las dos suma nada."""
    vacia = crear_seccion(anio_abierto, 4, "C")
    sin_docente = crear_seccion(anio_abierto, 5, "C", estudiantes=1)
    marcar(sin_docente, bimestres[3], ids_de(MATEMATICA))
    sin_estudiantes = crear_seccion(anio_abierto, 6, "D", docente)
    retirado = Estudiante.objects.create(
        seccion=sin_estudiantes,
        apellidos="RETIRADO",
        nombres="NOMBRE",
        estado=Estudiante.Estado.RETIRADO,
        fecha_estado=AYER,
    )
    assert retirado.pk

    estados = servicios.estado_de_las_secciones(institucion, bimestres[3], HOY)

    assert [(e.seccion, e.estado) for e in estados] == [
        (vacia, servicios.SIN_DOCENTE),
        (sin_docente, servicios.SIN_DOCENTE),
        (sin_estudiantes, servicios.SIN_ESTUDIANTES),
    ]
    assert all((e.notas_faltan, e.dias_sin_completar) == (0, 0) for e in estados)


def test_solo_las_secciones_del_anio_abierto_de_la_institucion(
    institucion, otra_institucion, anio_abierto, docente, bimestres
):
    propia = crear_seccion(anio_abierto, 1, "A", docente, estudiantes=1)
    cerrado = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    crear_seccion(cerrado, 1, "A", estudiantes=1)
    ajeno = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    crear_seccion(ajeno, 1, "B", estudiantes=1)

    estados = servicios.estado_de_las_secciones(institucion, bimestres[3], HOY)

    assert [e.seccion for e in estados] == [propia]


def test_el_estado_de_24_secciones_con_pocas_consultas(
    institucion, bimestres, veinticuatro, django_assert_max_num_queries
):
    """Riesgo «Rendimiento del mapa» (D3): consultas por lote, no por sección."""
    with django_assert_max_num_queries(4):
        estados = servicios.estado_de_las_secciones(institucion, bimestres[3], HOY)

    assert len(estados) == 24


# --- Resumen de la I.E. (D3 y D4) ---


def test_resumen_del_vigente(institucion, bimestres, veinticuatro):
    """Escenario «Resumen del vigente»: 9 de 22 y el pie con 4.º C y 6.º D."""
    estados = servicios.estado_de_las_secciones(institucion, bimestres[3], HOY)

    resumen = servicios.resumen_de_la_ie(estados, bimestres[3], HOY)

    assert (resumen.al_dia, resumen.consideradas) == (9, 22)
    assert resumen.dias_sin_completar == 13 * 10
    assert resumen.notas_faltan == 0
    assert resumen.texto_porcentaje == "100,0 %"
    assert not resumen.terminado
    assert resumen.texto_cierre == "Faltan 26 días para el cierre"
    assert resumen.nota_del_pie == (
        "Al día: sin notas que falten y sin días por completar. "
        "4.º C no tiene docente y 6.º D no tiene estudiantes."
    )


def test_resumen_de_un_periodo_anterior(institucion, bimestres, veinticuatro):
    """Escenario «Bimestre anterior»: «Terminado» y la fecha de término."""
    estados = servicios.estado_de_las_secciones(institucion, bimestres[1], HOY)

    resumen = servicios.resumen_de_la_ie(estados, bimestres[1], HOY)

    assert resumen.terminado
    assert resumen.texto_cierre == "Terminado"
    assert resumen.fecha_fin == bimestres[1].fecha_fin


@pytest.mark.parametrize(
    ("hoy", "texto"),
    [
        (datetime.date(2027, 12, 17), "Falta 1 día para el cierre"),
        (datetime.date(2027, 12, 18), "Hoy es el cierre"),
    ],
)
def test_los_ultimos_dias_del_vigente(institucion, bimestres, hoy, texto):
    resumen = servicios.resumen_de_la_ie([], bimestres[3], hoy)

    assert resumen.texto_cierre == texto


def test_el_porcentaje_de_la_ie_se_pondera_por_estudiantes(
    institucion, anio_abierto, docente, bimestres
):
    """Escenario «Promedio ponderado», con marcas reales: 4 × 50,0 y 1 × 100,0 dan 60,0."""
    periodo = bimestres[3]
    cuatro = crear_seccion(anio_abierto, 1, "A", docente, estudiantes=4)
    una = crear_seccion(anio_abierto, 1, "B", docente, estudiantes=1)
    completar_asistencia(cuatro, periodo, datetime.date(2027, 11, 8), docente)
    completar_asistencia(una, periodo, datetime.date(2027, 11, 8), docente)
    # Dos de los cuatro faltan el lunes 8: 50,0 %.
    Asistencia.objects.filter(
        jornada__seccion=cuatro, estudiante__in=list(cuatro.estudiantes.all()[:2])
    ).update(estado=Asistencia.Estado.FALTO)
    estados = servicios.estado_de_las_secciones(institucion, periodo, HOY)

    resumen = servicios.resumen_de_la_ie(estados, periodo, HOY)

    assert resumen.porcentaje == Decimal("60.0")


def test_las_sesiones_del_periodo_sin_el_material_de_referencia(
    otra_institucion, docente, crear_usuario, crear_sesion, material_de_referencia, bimestres
):
    """Por fecha de envío en Lima: el domingo 7 a las 23:30 ya es lunes 8 en UTC y no entra."""
    de_otra = crear_usuario("otra.ie", institucion=otra_institucion)

    crear_sesion(docente, creado_en=en_lima(2027, 11, 8, 0, 30))
    crear_sesion(docente, creado_en=en_lima(2027, 11, 7, 23, 30))
    crear_sesion(docente, creado_en=en_lima(2027, 11, 20, 10, 0), compartida=True)
    material_de_referencia(creado_en=en_lima(2027, 11, 20, 10, 0))
    crear_sesion(de_otra, creado_en=en_lima(2027, 11, 20, 10, 0))

    resumen = servicios.resumen_de_la_ie([], bimestres[3], HOY)

    assert resumen.sesiones == 2
