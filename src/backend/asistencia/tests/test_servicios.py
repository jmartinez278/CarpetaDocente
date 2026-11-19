"""Pruebas de los servicios de asistencia (spec asistencia-jornada; design de US-030, D2).

Todas fijan ``hoy``: ninguna depende del reloj. El 28-10-2026 es miércoles.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from asistencia import servicios
from asistencia.models import Asistencia, Jornada
from institucion.models import Estudiante, Periodo, Seccion

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 10, 28)
SABADO = datetime.date(2026, 10, 31)
AYER = HOY - datetime.timedelta(days=1)
MANANA = HOY + datetime.timedelta(days=1)

# US-031: el jueves 19-11-2026 es hoy y el lunes 16 es un día anterior que se corrige.
JUEVES = datetime.date(2026, 11, 19)
LUNES_16 = datetime.date(2026, 11, 16)
INICIO = datetime.date(2026, 3, 9)  # lunes: inicio del periodo 1


@pytest.fixture
def lista(seccion):
    """Cinco estudiantes activos, ya en orden alfabético."""
    nombres = [("AAA", "ANA"), ("BBB", "BETO"), ("CCC", "CARLA"), ("DDD", "DIEGO"), ("EEE", "ELSA")]
    return [Estudiante.objects.create(seccion=seccion, apellidos=a, nombres=n) for a, n in nombres]


@pytest.fixture
def ajeno(seccion):
    """Estudiante de otra sección del mismo año."""
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")
    return Estudiante.objects.create(seccion=otra, apellidos="ZZZ", nombres="ZOE")


@pytest.fixture
def anio_2026(seccion):
    """El año ABIERTO de la sección pasa a 2026, así los días de noviembre caen dentro."""
    anio = seccion.anio_escolar
    anio.anio = 2026
    anio.save()
    return anio


def crear_periodo(anio, numero, inicio):
    return Periodo.objects.create(
        anio_escolar=anio,
        numero=numero,
        fecha_inicio=inicio,
        fecha_fin=inicio + datetime.timedelta(days=60),
    )


def marcar(seccion, estudiante, estado, docente, nota="", fecha=HOY, hoy=HOY):
    return servicios.marcar(seccion, estudiante.pk, fecha, estado, nota, docente, hoy=hoy)


def restantes(seccion, estudiantes, docente, fecha=HOY, hoy=HOY):
    return servicios.marcar_restantes(seccion, [e.pk for e in estudiantes], fecha, docente, hoy=hoy)


# --- inicio_del_anio y se_puede_abrir (US-031, D1) ---


def test_inicio_del_anio_es_el_inicio_del_periodo_1(anio_2026):
    crear_periodo(anio_2026, 2, datetime.date(2026, 5, 18))
    crear_periodo(anio_2026, 1, INICIO)

    assert servicios.inicio_del_anio(anio_2026) == INICIO


def test_inicio_del_anio_sin_periodos_es_el_1_de_enero(anio_2026):
    assert servicios.inicio_del_anio(anio_2026) == datetime.date(2026, 1, 1)


@pytest.mark.parametrize(
    ("fecha", "esperado"),
    [
        (JUEVES, True),
        (LUNES_16, True),
        (INICIO, True),
        (datetime.date(2026, 3, 6), False),
        (JUEVES + datetime.timedelta(days=1), False),
        (datetime.date(2026, 11, 14), False),
    ],
    ids=["hoy", "dia-anterior", "inicio-exacto", "antes-del-inicio", "manana", "sabado"],
)
def test_se_puede_abrir(seccion, anio_2026, fecha, esperado):
    crear_periodo(anio_2026, 1, INICIO)

    assert servicios.se_puede_abrir(seccion, fecha, hoy=JUEVES) is esperado


def test_hoy_se_abre_aunque_sea_antes_del_inicio(seccion, anio_2026):
    crear_periodo(anio_2026, 1, INICIO)
    hoy = datetime.date(2026, 3, 4)  # miércoles

    assert servicios.se_puede_abrir(seccion, hoy, hoy=hoy) is True
    assert servicios.se_puede_abrir(seccion, hoy - datetime.timedelta(days=1), hoy=hoy) is False


def test_hoy_sabado_no_se_abre(seccion, anio_2026):
    sabado = datetime.date(2026, 11, 21)

    assert servicios.se_puede_abrir(seccion, sabado, hoy=sabado) is False


def test_anio_sin_periodos_abre_el_lunes_5_de_enero(seccion, anio_2026):
    assert servicios.se_puede_abrir(seccion, datetime.date(2026, 1, 5), hoy=JUEVES) is True


def test_a_las_23_30_de_lima_hoy_es_miercoles(seccion, anio_2026, monkeypatch):
    # Miércoles 18 a las 23:30 de Lima son las 04:30 UTC del jueves 19.
    utc = datetime.datetime(2026, 11, 19, 4, 30, tzinfo=datetime.UTC)
    monkeypatch.setattr(timezone, "now", lambda: utc)

    assert servicios.se_puede_abrir(seccion, datetime.date(2026, 11, 18)) is True
    assert servicios.se_puede_abrir(seccion, JUEVES) is False


# --- marcar ---


def test_el_primer_toque_crea_la_jornada(seccion, lista, docente):
    assert Jornada.objects.count() == 0

    marcar(seccion, lista[0], "ASISTIO", docente)

    jornada = Jornada.objects.get()
    assert (jornada.seccion, jornada.fecha, jornada.registrado_por) == (seccion, HOY, docente)
    assert Asistencia.objects.get().estado == "ASISTIO"


def test_dos_toques_dejan_una_sola_jornada(seccion, lista, docente):
    marcar(seccion, lista[0], "ASISTIO", docente)
    marcar(seccion, lista[1], "FALTO", docente)

    assert Jornada.objects.count() == 1
    assert Asistencia.objects.count() == 2


def test_el_mismo_guardado_dos_veces_deja_una_fila(seccion, lista, docente):
    marcar(seccion, lista[0], "TARDE", docente)
    marcar(seccion, lista[0], "TARDE", docente)

    assert Asistencia.objects.count() == 1
    assert Asistencia.objects.get().estado == "TARDE"


def test_dos_estados_seguidos_dejan_el_ultimo(seccion, lista, docente):
    marcar(seccion, lista[0], "ASISTIO", docente)
    marcar(seccion, lista[0], "FALTO", docente)

    assert Asistencia.objects.get().estado == "FALTO"


def test_el_segundo_toque_actualiza_la_hora_de_la_fila(seccion, lista, docente):
    """``actualizado_en`` es el dato del tiempo de la toma (design D1): el upsert lo mueve."""
    marcar(seccion, lista[0], "ASISTIO", docente)
    pasado = timezone.now() - datetime.timedelta(days=1)
    Asistencia.objects.update(actualizado_en=pasado)

    marcar(seccion, lista[0], "FALTO", docente)

    assert Asistencia.objects.get().actualizado_en > pasado


def test_si_falla_el_guardado_la_jornada_nueva_se_revierte(seccion, lista, docente, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("corte a mitad del guardado")

    monkeypatch.setattr(Asistencia.objects, "bulk_create", falla)

    with pytest.raises(RuntimeError):
        marcar(seccion, lista[0], "ASISTIO", docente)

    assert Jornada.objects.count() == 0


def test_si_falla_el_lote_la_jornada_nueva_se_revierte(seccion, lista, docente, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("corte a mitad del lote")

    monkeypatch.setattr(Asistencia.objects, "bulk_create", falla)

    with pytest.raises(RuntimeError):
        restantes(seccion, lista, docente)

    assert Jornada.objects.count() == 0


def test_la_nota_se_guarda_solo_con_justificado(seccion, lista, docente):
    marcar(seccion, lista[0], "JUSTIFICADO", docente, nota="Constancia entregada")
    marcar(seccion, lista[1], "FALTO", docente, nota="Debe borrarse")

    assert Asistencia.objects.get(estudiante=lista[0]).nota_justificacion == "Constancia entregada"
    assert Asistencia.objects.get(estudiante=lista[1]).nota_justificacion == ""


def test_la_nota_se_borra_al_pasar_a_otro_estado(seccion, lista, docente):
    marcar(seccion, lista[0], "JUSTIFICADO", docente, nota="Cita médica")
    marcar(seccion, lista[0], "ASISTIO", docente)

    assert Asistencia.objects.get().nota_justificacion == ""


def test_la_nota_de_100_caracteres_se_guarda(seccion, lista, docente):
    marcar(seccion, lista[0], "JUSTIFICADO", docente, nota="x" * 100)

    assert len(Asistencia.objects.get().nota_justificacion) == 100


def test_nota_de_101_caracteres_se_rechaza_sin_crear_jornada(seccion, lista, docente):
    with pytest.raises(ValidationError):
        marcar(seccion, lista[0], "JUSTIFICADO", docente, nota="x" * 101)

    assert Jornada.objects.count() == 0


def test_estado_invalido_se_rechaza_sin_crear_jornada(seccion, lista, docente):
    with pytest.raises(ValidationError):
        marcar(seccion, lista[0], "PERMISO", docente)

    assert Jornada.objects.count() == 0


@pytest.mark.parametrize("fecha", [AYER, MANANA], ids=["antes-del-inicio", "manana"])
def test_fecha_que_no_se_abre_se_rechaza_sin_crear_jornada(seccion, lista, docente, fecha):
    # El año de la sección es 2027: AYER (2026) cae antes de su inicio.
    with pytest.raises(servicios.FechaNoValida):
        marcar(seccion, lista[0], "ASISTIO", docente, fecha=fecha)

    assert Jornada.objects.count() == 0


def test_sabado_se_rechaza_sin_crear_jornada(seccion, lista, docente):
    with pytest.raises(servicios.FechaNoValida):
        marcar(seccion, lista[0], "ASISTIO", docente, fecha=SABADO, hoy=SABADO)

    assert Jornada.objects.count() == 0


def test_estudiante_de_otra_seccion_se_rechaza_sin_crear_jornada(seccion, lista, docente, ajeno):
    with pytest.raises(Estudiante.DoesNotExist):
        marcar(seccion, ajeno, "ASISTIO", docente)

    assert Jornada.objects.count() == 0


@pytest.mark.parametrize("estado_del_estudiante", ["RETIRADO", "TRASLADADO"])
def test_estudiante_no_activo_se_rechaza_sin_crear_jornada(
    seccion, lista, docente, estado_del_estudiante
):
    Estudiante.objects.filter(pk=lista[0].pk).update(estado=estado_del_estudiante)

    with pytest.raises(Estudiante.DoesNotExist):
        marcar(seccion, lista[0], "ASISTIO", docente)

    assert Jornada.objects.count() == 0


# --- marcar_restantes ---


def test_marcar_restantes_pone_asistio_a_los_sin_marcar(seccion, lista, docente):
    restantes(seccion, lista, docente)

    assert set(Asistencia.objects.values_list("estado", flat=True)) == {"ASISTIO"}
    assert Asistencia.objects.count() == 5
    assert Jornada.objects.count() == 1


def test_marcar_restantes_no_pisa_a_los_ya_marcados(seccion, lista, docente):
    marcar(seccion, lista[0], "FALTO", docente)
    marcar(seccion, lista[1], "JUSTIFICADO", docente, nota="Cita")

    restantes(seccion, lista, docente)

    estados = {a.estudiante_id: a.estado for a in Asistencia.objects.all()}
    assert estados[lista[0].pk] == "FALTO"
    assert estados[lista[1].pk] == "JUSTIFICADO"
    assert Asistencia.objects.get(estudiante=lista[1]).nota_justificacion == "Cita"
    assert {estados[e.pk] for e in lista[2:]} == {"ASISTIO"}


def test_un_id_ajeno_hace_fallar_todo_el_lote(seccion, lista, docente, ajeno):
    with pytest.raises(Estudiante.DoesNotExist):
        restantes(seccion, [*lista, ajeno], docente)

    assert Asistencia.objects.count() == 0
    assert Jornada.objects.count() == 0


def test_un_estudiante_no_activo_hace_fallar_todo_el_lote(seccion, lista, docente):
    Estudiante.objects.filter(pk=lista[4].pk).update(estado="RETIRADO")

    with pytest.raises(Estudiante.DoesNotExist):
        restantes(seccion, lista, docente)

    assert Asistencia.objects.count() == 0
    assert Jornada.objects.count() == 0


def test_marcar_restantes_rechaza_una_fecha_antes_del_inicio(seccion, lista, docente):
    with pytest.raises(servicios.FechaNoValida):
        restantes(seccion, lista, docente, fecha=AYER)

    assert Jornada.objects.count() == 0


def test_marcar_restantes_sin_ids_no_crea_jornada(seccion, lista, docente):
    restantes(seccion, [], docente)

    assert Jornada.objects.count() == 0


# --- guardados de un día anterior (US-031, D4 y D6) ---

NO_SE_ABREN = [
    pytest.param(JUEVES + datetime.timedelta(days=1), id="manana"),
    pytest.param(datetime.date(2026, 11, 14), id="sabado"),
    pytest.param(datetime.date(2026, 3, 6), id="antes-del-inicio"),
]


@pytest.fixture
def con_periodo(anio_2026):
    return crear_periodo(anio_2026, 1, INICIO)


def test_corregir_un_dia_anterior_de_falto_a_tarde(seccion, lista, docente, con_periodo):
    marcar(seccion, lista[0], "FALTO", docente, fecha=LUNES_16, hoy=JUEVES)

    marcar(seccion, lista[0], "TARDE", docente, fecha=LUNES_16, hoy=JUEVES)

    asistencia = Asistencia.objects.get()
    assert (asistencia.jornada.fecha, asistencia.estado) == (LUNES_16, "TARDE")


def test_dia_anterior_olvidado_crea_una_jornada_con_los_25(
    seccion, veinticinco, docente, anio_2026
):
    restantes(seccion, veinticinco, docente, fecha=LUNES_16, hoy=JUEVES)

    jornada = Jornada.objects.get()
    assert (jornada.seccion, jornada.fecha) == (seccion, LUNES_16)
    assert jornada.asistencias.filter(estado="ASISTIO").count() == 25


def test_un_retirado_despues_se_guarda_en_el_dia_anterior(seccion, lista, docente, anio_2026):
    retirar(lista[0], datetime.date(2026, 11, 18))
    retirar(lista[1], datetime.date(2026, 11, 18), "TRASLADADO")

    marcar(seccion, lista[0], "FALTO", docente, fecha=LUNES_16, hoy=JUEVES)
    restantes(seccion, lista, docente, fecha=LUNES_16, hoy=JUEVES)

    estados = {a.estudiante_id: a.estado for a in Asistencia.objects.all()}
    assert estados[lista[0].pk] == "FALTO"
    assert len(estados) == 5


@pytest.mark.parametrize("fecha_estado", [LUNES_16, datetime.date(2026, 11, 10), None])
def test_un_retirado_antes_no_se_guarda(seccion, lista, docente, anio_2026, fecha_estado):
    retirar(lista[0], fecha_estado)

    with pytest.raises(Estudiante.DoesNotExist):
        marcar(seccion, lista[0], "ASISTIO", docente, fecha=LUNES_16, hoy=JUEVES)
    with pytest.raises(Estudiante.DoesNotExist):
        restantes(seccion, lista, docente, fecha=LUNES_16, hoy=JUEVES)

    assert Jornada.objects.count() == 0


@pytest.mark.parametrize("fecha", NO_SE_ABREN)
def test_un_toque_de_una_fecha_que_no_se_abre_no_guarda(
    seccion, lista, docente, con_periodo, fecha
):
    with pytest.raises(servicios.FechaNoValida):
        marcar(seccion, lista[0], "ASISTIO", docente, fecha=fecha, hoy=JUEVES)

    assert Jornada.objects.count() == 0


@pytest.mark.parametrize("fecha", NO_SE_ABREN)
def test_un_lote_de_una_fecha_que_no_se_abre_no_guarda(seccion, lista, docente, con_periodo, fecha):
    with pytest.raises(servicios.FechaNoValida):
        restantes(seccion, lista, docente, fecha=fecha, hoy=JUEVES)

    assert Jornada.objects.count() == 0


def test_sin_cierre_de_periodos_ningun_periodo_esta_cerrado(seccion, anio_2026):
    assert servicios.periodo_cerrado(seccion, LUNES_16) is False
    assert servicios.periodo_cerrado(seccion, JUEVES) is False


def test_periodo_cerrado_es_una_fecha_no_valida():
    assert issubclass(servicios.PeriodoCerrado, servicios.FechaNoValida)


@pytest.mark.parametrize("guardado", ["toque", "lote"])
def test_en_un_periodo_cerrado_no_se_guarda_nada(
    seccion, lista, docente, anio_2026, monkeypatch, guardado
):
    monkeypatch.setattr(servicios, "periodo_cerrado", lambda seccion, fecha: True)

    with pytest.raises(servicios.PeriodoCerrado):
        if guardado == "toque":
            marcar(seccion, lista[0], "ASISTIO", docente, fecha=LUNES_16, hoy=JUEVES)
        else:
            restantes(seccion, lista, docente, fecha=LUNES_16, hoy=JUEVES)

    assert Jornada.objects.count() == 0
    assert RegistroActividad.objects.count() == 0


def test_jornada_completa_de_un_dia_anterior_cuenta_sus_activos(seccion, lista, docente, anio_2026):
    retirar(lista[4], datetime.date(2026, 11, 18))
    completas = RegistroActividad.objects.filter(operacion=Operacion.JORNADA_COMPLETA)

    for estudiante in lista[:4]:
        marcar(seccion, estudiante, "ASISTIO", docente, fecha=LUNES_16, hoy=JUEVES)
    assert not completas.exists()

    marcar(seccion, lista[4], "ASISTIO", docente, fecha=LUNES_16, hoy=JUEVES)
    assert completas.count() == 1


def test_jornada_completa_de_un_dia_anterior_sin_los_retirados_antes(
    seccion, lista, docente, anio_2026
):
    retirar(lista[4], datetime.date(2026, 11, 10))

    restantes(seccion, lista[:4], docente, fecha=LUNES_16, hoy=JUEVES)

    assert RegistroActividad.objects.filter(operacion=Operacion.JORNADA_COMPLETA).count() == 1


# --- lista_del_dia ---


def test_lista_del_dia_sin_jornada_no_la_crea(seccion, lista):
    datos = servicios.lista_del_dia(seccion, HOY)

    assert Jornada.objects.count() == 0
    assert datos.jornada is None
    assert (datos.marcados, datos.total, datos.sin_marcar) == (0, 5, 5)
    assert not datos.completa
    assert [f.estado for f in datos.filas] == [None] * 5


def test_lista_del_dia_ordena_y_numera_de_1_a_m_solo_los_activos(seccion, lista):
    Estudiante.objects.filter(pk=lista[1].pk).update(estado="TRASLADADO")
    Estudiante.objects.filter(pk=lista[3].pk).update(estado="RETIRADO")

    datos = servicios.lista_del_dia(seccion, HOY)

    assert [(f.numero, f.estudiante.apellidos) for f in datos.filas] == [
        (1, "AAA"),
        (2, "CCC"),
        (3, "EEE"),
    ]
    assert [e.apellidos for e in datos.no_activos] == ["BBB", "DDD"]
    assert datos.total == 3


def test_lista_del_dia_cuenta_el_avance_y_los_totales(seccion, lista, docente):
    marcar(seccion, lista[0], "ASISTIO", docente)
    marcar(seccion, lista[1], "ASISTIO", docente)
    marcar(seccion, lista[2], "TARDE", docente)
    marcar(seccion, lista[3], "JUSTIFICADO", docente, nota="Cita")

    datos = servicios.lista_del_dia(seccion, HOY)

    assert (datos.marcados, datos.total, datos.sin_marcar) == (4, 5, 1)
    assert datos.totales == {"ASISTIO": 2, "TARDE": 1, "FALTO": 0, "JUSTIFICADO": 1}
    assert datos.filas[3].nota == "Cita"
    assert datos.filas[4].estado is None
    assert not datos.completa


def test_lista_del_dia_es_completa_cuando_los_activos_tienen_estado(seccion, lista, docente):
    Estudiante.objects.filter(pk=lista[4].pk).update(estado="RETIRADO")
    for estudiante in lista[:4]:
        marcar(seccion, estudiante, "ASISTIO", docente)

    datos = servicios.lista_del_dia(seccion, HOY)

    assert datos.completa
    assert datos.sin_marcar == 0


def test_lista_del_dia_hace_tres_consultas(seccion, lista, docente, django_assert_num_queries):
    marcar(seccion, lista[0], "ASISTIO", docente)

    with django_assert_num_queries(3):  # jornada, estudiantes y asistencias
        servicios.lista_del_dia(seccion, HOY)


def test_lista_del_dia_de_otra_fecha_no_mezcla_jornadas(seccion, lista, docente):
    marcar(seccion, lista[0], "ASISTIO", docente)

    datos = servicios.lista_del_dia(seccion, MANANA)

    assert datos.jornada is None
    assert datos.marcados == 0


# --- activos_del_dia y lista_del_dia de un día anterior (US-031, D4) ---


def retirar(estudiante, fecha_estado, estado="RETIRADO"):
    Estudiante.objects.filter(pk=estudiante.pk).update(estado=estado, fecha_estado=fecha_estado)


@pytest.mark.parametrize("estado", ["RETIRADO", "TRASLADADO"])
def test_retirado_despues_del_dia_abierto_es_activo_ese_dia(seccion, lista, estado):
    retirar(lista[1], datetime.date(2026, 11, 18), estado)

    assert lista[1] in servicios.activos_del_dia(seccion, LUNES_16)
    datos = servicios.lista_del_dia(seccion, LUNES_16)
    assert [f.estudiante.apellidos for f in datos.filas] == ["AAA", "BBB", "CCC", "DDD", "EEE"]
    assert datos.filas[1].numero == 2
    assert datos.no_activos == []
    assert datos.total == 5


def test_retirado_el_mismo_dia_queda_fuera(seccion, lista):
    retirar(lista[1], LUNES_16)

    assert lista[1] not in servicios.activos_del_dia(seccion, LUNES_16)
    datos = servicios.lista_del_dia(seccion, LUNES_16)
    assert [e.apellidos for e in datos.no_activos] == ["BBB"]
    assert datos.total == 4


def test_retirado_sin_fecha_queda_fuera_de_un_dia_anterior(seccion, lista):
    retirar(lista[1], None)

    assert lista[1] not in servicios.activos_del_dia(seccion, LUNES_16)
    datos = servicios.lista_del_dia(seccion, LUNES_16)
    assert [e.apellidos for e in datos.no_activos] == ["BBB"]
    assert [f.numero for f in datos.filas] == [1, 2, 3, 4]


def test_retirado_despues_no_es_activo_hoy(seccion, lista):
    retirar(lista[1], datetime.date(2026, 11, 18))

    assert lista[1] not in servicios.activos_del_dia(seccion, JUEVES)
    assert [e.apellidos for e in servicios.lista_del_dia(seccion, JUEVES).no_activos] == ["BBB"]


def test_dia_anterior_con_un_retirado_despues_queda_incompleto(seccion, veinticinco, docente):
    retirado = veinticinco[-1]
    retirar(retirado, datetime.date(2026, 11, 18))
    jornada = Jornada.objects.create(seccion=seccion, fecha=LUNES_16, registrado_por=docente)
    Asistencia.objects.bulk_create(
        [Asistencia(jornada=jornada, estudiante=e, estado="ASISTIO") for e in veinticinco[:-1]]
    )

    datos = servicios.lista_del_dia(seccion, LUNES_16)

    assert (datos.marcados, datos.total, datos.sin_marcar) == (24, 25, 1)
    assert not datos.completa
    assert servicios._completa_o_vacia(seccion, LUNES_16) is False


def test_dia_anterior_completo_no_cuenta_a_los_retirados_antes(seccion, veinticinco, docente):
    retirar(veinticinco[-1], datetime.date(2026, 11, 2))
    jornada = Jornada.objects.create(seccion=seccion, fecha=LUNES_16, registrado_por=docente)
    Asistencia.objects.bulk_create(
        [Asistencia(jornada=jornada, estudiante=e, estado="ASISTIO") for e in veinticinco[:-1]]
    )

    assert servicios.lista_del_dia(seccion, LUNES_16).completa
    assert servicios._completa_o_vacia(seccion, LUNES_16) is True


# --- pendiente_hoy ---


def test_pendiente_hoy_con_la_jornada_sin_completar(seccion, lista):
    assert servicios.pendiente_hoy(seccion, hoy=HOY) is True


def test_pendiente_hoy_es_falso_con_la_jornada_completa(seccion, lista, docente):
    restantes(seccion, lista, docente)

    assert servicios.pendiente_hoy(seccion, hoy=HOY) is False


def test_pendiente_hoy_es_falso_en_sabado(seccion, lista):
    assert servicios.pendiente_hoy(seccion, hoy=SABADO) is False


def test_pendiente_hoy_es_falso_sin_estudiantes_activos(seccion):
    assert servicios.pendiente_hoy(seccion, hoy=HOY) is False


# --- es_dia_de_clases, texto_fecha, saludo ---


@pytest.mark.parametrize(
    ("fecha", "esperado"),
    [
        (datetime.date(2026, 10, 26), True),
        (datetime.date(2026, 10, 30), True),
        (datetime.date(2026, 10, 31), False),
        (datetime.date(2026, 11, 1), False),
    ],
)
def test_es_dia_de_clases_es_de_lunes_a_viernes(fecha, esperado):
    assert servicios.es_dia_de_clases(fecha) is esperado


@pytest.mark.parametrize(
    ("fecha", "esperado"),
    [
        (datetime.date(2026, 10, 28), "Miércoles 28 de octubre"),
        (datetime.date(2026, 11, 2), "Lunes 2 de noviembre"),
        (datetime.date(2026, 12, 25), "Viernes 25 de diciembre"),
        (datetime.date(2027, 3, 6), "Sábado 6 de marzo"),
    ],
)
def test_texto_fecha_en_espanol(fecha, esperado):
    assert servicios.texto_fecha(fecha) == esperado


@pytest.mark.parametrize(
    ("hora", "esperado"),
    [
        (4, "Buenos días"),
        (11, "Buenos días"),
        (12, "Buenas tardes"),
        (18, "Buenas tardes"),
        (19, "Buenas noches"),
        (23, "Buenas noches"),
    ],
)
def test_saludo_segun_la_hora(hora, esperado):
    assert servicios.saludo(hora) == esperado


# --- semana (selector de la pantalla) ---


def test_semana_de_un_miercoles():
    semana = servicios.semana(datetime.date(2026, 10, 28))

    assert semana.etiqueta == "Semana del 26 al 30 de octubre"
    assert [d.abreviatura for d in semana.dias] == ["Lun", "Mar", "Mié", "Jue", "Vie"]
    assert [d.fecha.day for d in semana.dias] == [26, 27, 28, 29, 30]
    assert [d.es_hoy for d in semana.dias] == [False, False, True, False, False]
    assert semana.dias[2].etiqueta == "Mié 28 de octubre, hoy"
    assert semana.dias[0].etiqueta == "Lun 26 de octubre, no disponible"


def test_semana_que_cruza_de_mes():
    semana = servicios.semana(datetime.date(2026, 10, 1))

    assert semana.etiqueta == "Semana del 28 de septiembre al 2 de octubre"


@pytest.mark.parametrize("dia", [31, 1], ids=["sabado", "domingo"])
def test_en_fin_de_semana_es_la_semana_que_acaba_de_pasar_sin_hoy(dia):
    fecha = datetime.date(2026, 10, 31) if dia == 31 else datetime.date(2026, 11, 1)

    semana = servicios.semana(fecha)

    assert semana.etiqueta == "Semana del 26 al 30 de octubre"
    assert not any(d.es_hoy for d in semana.dias)


# --- lo que la pantalla lee de una fila y de la lista ---


@pytest.mark.parametrize(
    ("estado", "palabra", "siguiente", "clase"),
    [
        (None, "Sin marcar", "Asistió", "estado--sin-marcar"),
        ("ASISTIO", "Asistió", "Faltó", "estado--asistio"),
        ("FALTO", "Faltó", "Tarde", "estado--falto"),
        ("TARDE", "Tarde", "Justificado", "estado--tarde"),
        ("JUSTIFICADO", "Justificado", "Asistió", "estado--justificado"),
    ],
)
def test_la_fila_dice_su_estado_y_el_siguiente(estado, palabra, siguiente, clase):
    fila = servicios.Fila(numero=1, estudiante=None, estado=estado, nota="")

    assert (fila.palabra, fila.siguiente, fila.clase) == (palabra, siguiente, clase)


def test_el_resumen_va_en_el_orden_de_la_pantalla():
    lista = servicios.ListaDeHoy(
        jornada=None,
        filas=[],
        no_activos=[],
        totales={"ASISTIO": 21, "FALTO": 2, "TARDE": 1, "JUSTIFICADO": 1},
    )

    assert lista.resumen == "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1"


@pytest.mark.parametrize(
    ("sin_marcar", "texto"),
    [(0, ""), (1, "Marcar el restante como Asistió"), (7, "Marcar los 7 restantes como Asistió")],
)
def test_el_texto_de_marcar_los_restantes(sin_marcar, texto):
    filas = [
        servicios.Fila(numero=n, estudiante=None, estado=None, nota="") for n in range(sin_marcar)
    ]
    filas += [servicios.Fila(numero=99, estudiante=None, estado="ASISTIO", nota="")]
    lista = servicios.ListaDeHoy(jornada=None, filas=filas, no_activos=[])

    assert lista.texto_marcar_restantes == texto
