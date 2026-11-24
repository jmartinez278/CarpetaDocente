"""Estado de las secciones, periodo elegido y resumen de la I.E. (US-040, D3 y D4; spec
consolidados-direccion)."""

import datetime
from decimal import Decimal

import pytest
from django.http import Http404

from asistencia.models import Asistencia
from catalogo.models import Area
from cuentas.models import Usuario
from direccion import servicios
from direccion.tests.conftest import HOY, completar_asistencia, crear_seccion
from institucion.models import AnioEscolar, Estudiante, Periodo
from notas.servicios import ANTERIOR, VIGENTE
from notas.tests.conftest import (
    EDUCACION_FISICA,
    INGLES,
    MATEMATICA,
    competencia,
    ids_de,
    marcar,
    poner_nota,
)

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


# --- Sesiones de una sección y docentes de curso del grado (D6) ---

# Hoy es el lunes 22; la semana anterior va del 15 al 19 y el IV bimestre empezó el lunes 8.
VIERNES_19 = datetime.date(2027, 11, 19)
FIN_DEL_BIMESTRE = datetime.date(2027, 12, 18)
DESPUES_DEL_BIMESTRE = datetime.date(2027, 12, 22)


@pytest.fixture
def dos_a(anio_abierto, docente, bimestres, areas_a_cargo):
    """2.º A con su tutora (``docente``)."""
    return crear_seccion(anio_abierto, 2, "A", docente, estudiantes=2)


@pytest.fixture
def docente_de_curso(crear_usuario):
    return crear_usuario("jsoto", first_name="Julia", last_name="Soto")


@pytest.fixture
def ingles(db):
    return Area.objects.get(codigo_siagie=INGLES)


def envio(dia, hora=10):
    """La fecha de envío: ``hora`` de ``dia`` en Lima."""
    return en_lima(dia.year, dia.month, dia.day, hora, 0)


def noviembre(dia):
    return datetime.date(2027, 11, dia)


def titulos(sesiones):
    return [s.titulo for s in sesiones]


def test_las_sesiones_de_la_seccion_son_las_de_su_tutora_para_su_grado(
    dos_a,
    docente,
    otra_docente,
    docente_de_curso,
    ingles,
    crear_sesion,
    material_de_referencia,
    bimestres,
):
    cuando = envio(VIERNES_19)
    crear_sesion(docente, creado_en=cuando, titulo="Propia del grado")
    crear_sesion(docente, creado_en=cuando, titulo="Sin compartir", compartida=False)
    crear_sesion(docente, creado_en=cuando, titulo="Otro grado", grado=3)
    crear_sesion(otra_docente, creado_en=cuando, titulo="De la colega tutora de 2.º B")
    crear_sesion(docente_de_curso, creado_en=cuando, titulo="De Inglés", area=ingles)
    material_de_referencia(creado_en=cuando, titulo="Referencia", grado=1, grado_hasta=6)

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    assert sorted(titulos(datos.sesiones)) == ["Propia del grado", "Sin compartir"]


def test_las_sesiones_se_agrupan_por_la_fecha_de_envio_en_lima(
    dos_a, docente, crear_sesion, bimestres
):
    """El jueves 18 a las 23:30 en Lima ya es viernes 19 en UTC: cuenta el día de Lima."""
    crear_sesion(docente, creado_en=en_lima(2027, 11, 18, 23, 30), titulo="Jueves tarde")
    crear_sesion(docente, creado_en=en_lima(2027, 11, 7, 23, 30), titulo="Antes del bimestre")
    crear_sesion(docente, creado_en=en_lima(2027, 11, 8, 0, 30), titulo="Primer minuto")
    crear_sesion(docente, creado_en=en_lima(2027, 12, 18, 23, 59), titulo="Último minuto")
    crear_sesion(docente, creado_en=en_lima(2027, 12, 19, 0, 30), titulo="Después del bimestre")

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], DESPUES_DEL_BIMESTRE)

    assert sorted(datos.por_dia) == [noviembre(8), noviembre(18), FIN_DEL_BIMESTRE]


def test_sin_tutora_no_hay_sesiones_de_la_seccion(anio_abierto, docente, crear_sesion, bimestres):
    sin_tutora = crear_seccion(anio_abierto, 2, "C", estudiantes=1)
    crear_sesion(docente, creado_en=envio(VIERNES_19))

    datos = servicios.sesiones_de_la_seccion(sin_tutora, bimestres[3], HOY)

    assert datos.sesiones == []
    assert datos.dias_con_sesion == 0


def test_dias_con_sesion_de_la_tutora_nueve_de_once(dos_a, docente, crear_sesion, bimestres):
    # Del 8 al 22 de noviembre hay 11 días de clase; la tutora envió en 9 de ellos.
    for dia in (8, 9, 10, 11, 12, 15, 16, 17, 22):
        crear_sesion(docente, creado_en=envio(noviembre(dia)))
    crear_sesion(docente, creado_en=envio(noviembre(8), 15))  # dos el mismo día
    crear_sesion(docente, creado_en=envio(noviembre(13)))  # sábado: no es día de clase

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    assert (datos.dias_con_sesion, len(datos.dias_de_clase)) == (9, 11)
    assert datos.numero(noviembre(8)) == 2


def test_las_sesiones_de_un_dia_van_de_la_mas_reciente_a_la_mas_antigua(
    dos_a, docente, crear_sesion, bimestres
):
    crear_sesion(docente, creado_en=envio(VIERNES_19, 8), titulo="Temprano")
    crear_sesion(docente, creado_en=envio(VIERNES_19, 15), titulo="Tarde")

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    assert titulos(datos.del_dia(VIERNES_19)) == ["Tarde", "Temprano"]


def test_las_sesiones_de_la_seccion_en_una_consulta(
    dos_a, docente, crear_sesion, bimestres, django_assert_max_num_queries
):
    for dia in range(8, 13):
        crear_sesion(docente, creado_en=envio(noviembre(dia)))

    with django_assert_max_num_queries(1):
        datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)
        assert [(s.area.nombre, s.autor.last_name) for s in datos.sesiones]


def test_sesiones_de_curso_del_grado_dentro_y_fuera(
    institucion,
    docente_de_curso,
    ingles,
    comunicacion,
    crear_sesion,
    areas_a_cargo,
    bimestres,
    material_de_referencia,
):
    cuando = envio(VIERNES_19)
    crear_sesion(docente_de_curso, creado_en=cuando, area=ingles, titulo="Inglés de 2.º")
    crear_sesion(docente_de_curso, creado_en=cuando, area=ingles, titulo="Inglés de 3.º", grado=3)
    crear_sesion(docente_de_curso, creado_en=cuando, area=comunicacion, titulo="Comunicación")
    crear_sesion(
        docente_de_curso,
        creado_en=en_lima(2027, 11, 5, 10, 0),
        area=ingles,
        titulo="Antes del bimestre",
    )
    material_de_referencia(
        creado_en=cuando, titulo="Referencia", area=ingles, grado=1, grado_hasta=6
    )

    docentes = servicios.sesiones_de_curso_del_grado(institucion, 2, bimestres[3])

    assert [(d.autor, d.area) for d in docentes] == [(docente_de_curso, ingles)]
    assert sorted(titulos(docentes[0].sesiones)) == ["Inglés de 2.º"]


def test_sesiones_de_curso_de_otra_institucion_no_entran(
    institucion, otra_institucion, crear_usuario, ingles, crear_sesion, areas_a_cargo, bimestres
):
    de_otra = crear_usuario("ajena.curso", institucion=otra_institucion)
    crear_sesion(de_otra, creado_en=envio(VIERNES_19), area=ingles)

    assert servicios.sesiones_de_curso_del_grado(institucion, 2, bimestres[3]) == []


def test_un_area_que_no_esta_a_cargo_del_docente_de_curso_no_entra(
    institucion, docente_de_curso, ingles, crear_sesion, bimestres
):
    # Sin ``areas_a_cargo``: Inglés no es del docente de curso en esta I.E.
    crear_sesion(docente_de_curso, creado_en=envio(VIERNES_19), area=ingles)

    assert servicios.sesiones_de_curso_del_grado(institucion, 2, bimestres[3]) == []


def test_cada_docente_de_curso_con_sus_dias_y_su_ultima_fecha(
    institucion, crear_usuario, docente_de_curso, ingles, crear_sesion, areas_a_cargo, bimestres
):
    otro = crear_usuario("aaguilar", first_name="Beto", last_name="Aguilar")
    educacion_fisica = Area.objects.get(codigo_siagie=EDUCACION_FISICA)
    crear_sesion(docente_de_curso, creado_en=envio(noviembre(9)), area=ingles)
    crear_sesion(docente_de_curso, creado_en=envio(noviembre(9), 15), area=ingles)
    crear_sesion(docente_de_curso, creado_en=envio(VIERNES_19), area=ingles, titulo="Última")
    crear_sesion(otro, creado_en=envio(VIERNES_19), area=educacion_fisica, titulo="De E. F.")

    docentes = servicios.sesiones_de_curso_del_grado(institucion, 2, bimestres[3])

    # Por apellidos: Aguilar antes que Soto.
    assert [d.autor for d in docentes] == [otro, docente_de_curso]
    assert docentes[0].texto_dias == "1 día con sesión · Última: vie 19 nov"
    assert docentes[1].texto_dias == "2 días con sesión · Última: vie 19 nov"
    assert titulos(docentes[1].del_dia(VIERNES_19)) == ["Última"]
    assert docentes[1].del_dia(noviembre(18)) == []


def test_las_sesiones_de_curso_en_una_consulta(
    institucion,
    docente_de_curso,
    ingles,
    crear_sesion,
    areas_a_cargo,
    bimestres,
    django_assert_max_num_queries,
):
    for dia in range(8, 13):
        crear_sesion(docente_de_curso, creado_en=envio(noviembre(dia)), area=ingles)

    with django_assert_max_num_queries(1):
        docentes = servicios.sesiones_de_curso_del_grado(institucion, 2, bimestres[3])
        assert [(s.area.nombre, s.autor.last_name) for d in docentes for s in d.sesiones]


# Día elegido y semana: solo con las sesiones de la sección


def test_hoy_con_sesiones_es_el_dia_por_defecto(dos_a, docente, crear_sesion, bimestres):
    crear_sesion(docente, creado_en=envio(HOY))
    crear_sesion(docente, creado_en=envio(VIERNES_19))

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    assert datos.dia_elegido(None) == HOY


def test_sin_sesiones_hoy_el_dia_por_defecto_es_el_ultimo_con_sesiones(
    dos_a, docente, crear_sesion, bimestres
):
    # Escenario «Semana de la sección»: hoy sin sesiones y el viernes anterior con 2.
    crear_sesion(docente, creado_en=envio(VIERNES_19, 8))
    crear_sesion(docente, creado_en=envio(VIERNES_19, 9))
    crear_sesion(docente, creado_en=envio(noviembre(16)))

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)
    semana = datos.semana(datos.dia_elegido(None), url_de=str)

    assert datos.dia_elegido(None) == VIERNES_19
    assert semana.etiqueta == "Semana del 15 al 19 de noviembre"
    assert [d.numero for d in semana.dias] == [0, 1, 0, 0, 2]
    assert [d.elegido for d in semana.dias] == [False, False, False, False, True]


def test_un_dia_con_solo_una_sesion_de_curso_no_es_el_dia_por_defecto(
    dos_a, docente, docente_de_curso, ingles, crear_sesion, bimestres
):
    crear_sesion(docente_de_curso, creado_en=envio(HOY), area=ingles)
    crear_sesion(docente, creado_en=envio(VIERNES_19))

    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    assert datos.dia_elegido(None) == VIERNES_19
    assert datos.numero(HOY) == 0


def test_sin_ninguna_sesion_el_dia_por_defecto_es_el_ultimo_dia_de_clase_hasta_hoy(
    dos_a, bimestres
):
    sabado = noviembre(27)

    assert servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY).dia_elegido(None) == HOY
    assert servicios.sesiones_de_la_seccion(dos_a, bimestres[3], sabado).dia_elegido(
        None
    ) == noviembre(26)


def test_un_bimestre_terminado_abre_en_su_ultimo_dia_de_clase(dos_a, bimestres):
    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], DESPUES_DEL_BIMESTRE)

    assert datos.dia_elegido(None) == datetime.date(2027, 12, 17)


def test_el_dia_pedido_vale_si_es_de_clase_dentro_del_bimestre_y_hasta_hoy(
    dos_a, docente, crear_sesion, bimestres
):
    crear_sesion(docente, creado_en=envio(VIERNES_19))
    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    assert datos.dia_elegido("2027-11-16") == noviembre(16)
    for pedido in ("2027-11-23", "2027-11-13", "2027-11-05", "2027-12-20", "basura", "", None):
        assert datos.dia_elegido(pedido) == VIERNES_19


def test_las_flechas_de_la_semana(dos_a, bimestres):
    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    primera = datos.semana(noviembre(10), url_de=str)
    anterior = datos.semana(VIERNES_19, url_de=str)
    actual = datos.semana(HOY, url_de=str)

    assert (primera.anterior, primera.siguiente) == (None, "2027-11-17")
    assert (anterior.anterior, anterior.siguiente) == ("2027-11-12", "2027-11-22")
    assert (actual.anterior, actual.siguiente) == ("2027-11-15", None)


def test_los_dias_fuera_del_bimestre_o_despues_de_hoy_no_son_enlaces(dos_a, bimestres):
    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], HOY)

    actual = datos.semana(HOY, url_de=str)

    assert [d.disponible for d in actual.dias] == [True, False, False, False, False]
    assert [d.url for d in actual.dias] == ["2027-11-22", None, None, None, None]


def test_la_flecha_siguiente_no_pasa_del_fin_del_bimestre(dos_a, bimestres):
    datos = servicios.sesiones_de_la_seccion(dos_a, bimestres[3], DESPUES_DEL_BIMESTRE)

    ultima = datos.semana(datetime.date(2027, 12, 17), url_de=str)

    assert ultima.siguiente is None
    assert ultima.anterior == "2027-12-10"


# --- Sección de la dirección (D2) ---


def test_la_seccion_de_la_direccion_es_la_del_anio_abierto_de_su_institucion(
    dos_a, direccion, django_assert_num_queries
):
    seccion = servicios.seccion_de_la_direccion(direccion, dos_a.pk)

    assert seccion == dos_a
    # El año y la tutora ya vienen cargados: leerlos no es otra consulta.
    with django_assert_num_queries(0):
        assert seccion.anio_escolar.institucion_id == direccion.institucion_id
        assert seccion.docente.last_name == "Quispe"


def test_otra_institucion_es_pagina_no_encontrada(dos_a, crear_usuario, otra_institucion):
    otra = crear_usuario("dir.otra", Usuario.Rol.DIRECCION, institucion=otra_institucion)

    with pytest.raises(Http404):
        servicios.seccion_de_la_direccion(otra, dos_a.pk)


def test_un_anio_cerrado_es_pagina_no_encontrada(institucion, direccion, docente):
    anio = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    cerrada = crear_seccion(anio, 2, "A", docente=docente)

    with pytest.raises(Http404):
        servicios.seccion_de_la_direccion(direccion, cerrada.pk)


@pytest.mark.parametrize("id_seccion", [0, 99999, "no-es-un-numero", None])
def test_una_seccion_inexistente_es_pagina_no_encontrada(dos_a, direccion, id_seccion):
    with pytest.raises(Http404):
        servicios.seccion_de_la_direccion(direccion, id_seccion)


def test_una_cuenta_que_no_es_la_direccion_no_tiene_secciones(dos_a, docente):
    with pytest.raises(Http404):
        servicios.seccion_de_la_direccion(docente, dos_a.pk)
