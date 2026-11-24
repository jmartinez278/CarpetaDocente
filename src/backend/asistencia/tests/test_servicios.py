"""Pruebas de los servicios de asistencia (spec asistencia-jornada; design de US-030, D2).

Todas fijan ``hoy``: ninguna depende del reloj. El 28-10-2026 es miércoles.
"""

import datetime
from decimal import Decimal

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


# --- semana (selector de la pantalla; US-031, D3) ---


def semana(abierto, hoy=JUEVES, inicio=INICIO):
    """El selector con una URL reconocible: ``/AAAA-MM-DD`` para cada día."""
    return servicios.semana(abierto, hoy, inicio, url_de=lambda fecha: f"/{fecha.isoformat()}")


def fechas(dias):
    return [d.fecha.day for d in dias]


def test_selector_un_jueves():
    """Escenario "Selector un jueves"."""
    s = semana(JUEVES)

    assert s.etiqueta == "Semana del 16 al 20 de noviembre"
    assert [d.abreviatura for d in s.dias] == ["Lun", "Mar", "Mié", "Jue", "Vie"]
    assert fechas(s.dias) == [16, 17, 18, 19, 20]
    assert [d.es_hoy for d in s.dias] == [False, False, False, True, False]
    assert [d.elegido for d in s.dias] == [False, False, False, True, False]
    assert [d.disponible for d in s.dias] == [True, True, True, True, False]
    assert [d.url for d in s.dias] == [
        "/2026-11-16",
        "/2026-11-17",
        "/2026-11-18",
        "/2026-11-19",
        None,
    ]
    assert s.dias[3].etiqueta == "Jue 19 de noviembre, hoy"
    assert s.dias[0].etiqueta == "Lun 16 de noviembre"
    assert s.dias[4].etiqueta == "Vie 20 de noviembre, no disponible"
    assert s.anterior == "/2026-11-12"
    assert s.siguiente is None


def test_selector_en_un_dia_pasado():
    """Escenario "Selector en un día pasado": el miércoles de la semana anterior."""
    s = semana(datetime.date(2026, 11, 11))

    assert fechas(s.dias) == [9, 10, 11, 12, 13]
    assert [d.elegido for d in s.dias] == [False, False, True, False, False]
    assert not any(d.es_hoy for d in s.dias)
    assert all(d.disponible for d in s.dias)
    assert s.dias[2].etiqueta == "Mié 11 de noviembre, abierto"
    assert s.dias[1].etiqueta == "Mar 10 de noviembre"
    assert s.anterior == "/2026-11-04"
    assert s.siguiente == "/2026-11-18"


def test_selector_la_flecha_siguiente_no_pasa_de_hoy():
    s = semana(datetime.date(2026, 11, 13))

    assert s.siguiente == "/2026-11-19"


def test_selector_la_flecha_siguiente_de_la_semana_de_hoy_no_responde():
    for dia in (16, 17, 18, 19):
        assert semana(datetime.date(2026, 11, dia)).siguiente is None


def test_selector_primera_semana_del_ano():
    """Escenario "Primera semana del año": empieza un miércoles."""
    inicio = datetime.date(2026, 3, 11)

    s = semana(inicio, hoy=datetime.date(2026, 3, 12), inicio=inicio)

    assert fechas(s.dias) == [9, 10, 11, 12, 13]
    assert [d.disponible for d in s.dias] == [False, False, True, True, False]
    assert [d.url for d in s.dias][:2] == [None, None]
    assert s.dias[0].etiqueta == "Lun 9 de marzo, no disponible"
    assert s.dias[2].etiqueta == "Mié 11 de marzo, abierto"
    assert s.anterior is None
    assert s.siguiente is None


def test_selector_la_flecha_anterior_cae_antes_del_inicio_y_abre_el_primer_dia():
    inicio = datetime.date(2026, 11, 11)  # miércoles

    s = semana(datetime.date(2026, 11, 17), inicio=inicio)

    assert s.anterior == "/2026-11-11"


def test_selector_la_flecha_anterior_sin_dias_en_la_semana_anterior_no_responde():
    # El inicio es el sábado 14: la semana del 9 al 13 no tiene días que abrir.
    s = semana(JUEVES, inicio=datetime.date(2026, 11, 14))

    assert s.anterior is None


def test_selector_el_inicio_un_viernes_deja_a_la_flecha_abrir_ese_viernes():
    s = semana(JUEVES, inicio=datetime.date(2026, 11, 13))

    assert s.anterior == "/2026-11-13"


def test_selector_con_hoy_antes_del_inicio_solo_hoy_se_abre():
    hoy = datetime.date(2026, 3, 5)

    s = semana(hoy, hoy=hoy, inicio=datetime.date(2026, 3, 9))

    assert [d.disponible for d in s.dias] == [False, False, False, True, False]
    assert s.dias[3].etiqueta == "Jue 5 de marzo, hoy"
    assert (s.anterior, s.siguiente) == (None, None)


@pytest.mark.parametrize("dia", [21, 22], ids=["sabado", "domingo"])
def test_en_fin_de_semana_es_la_semana_que_acaba_de_pasar_sin_elegido(dia):
    hoy = datetime.date(2026, 11, dia)

    s = semana(hoy, hoy=hoy)

    assert s.etiqueta == "Semana del 16 al 20 de noviembre"
    assert not any(d.es_hoy or d.elegido for d in s.dias)
    assert all(d.disponible for d in s.dias)
    assert s.anterior == "/2026-11-13", "el viernes de referencia, una semana antes"
    assert s.siguiente is None


def test_semana_que_cruza_de_mes():
    s = semana(datetime.date(2026, 10, 1), hoy=datetime.date(2026, 10, 1))

    assert s.etiqueta == "Semana del 28 de septiembre al 2 de octubre"


def test_las_urls_por_defecto_son_las_fechas():
    s = servicios.semana(JUEVES, JUEVES, INICIO)

    assert s.dias[0].url == "2026-11-16"
    assert s.anterior == "2026-11-12"


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


# --- US-040, D5. Asistencia por periodo ---

# El IV bimestre de 2027 va del lunes 8 de noviembre al viernes 17 de diciembre; hoy es el
# lunes 22 de noviembre: 11 días de clase hasta hoy y 10 hasta ayer.
IV_INICIO = datetime.date(2027, 11, 8)
IV_FIN = datetime.date(2027, 12, 17)
HOY_IV = datetime.date(2027, 11, 22)
MARTES_16 = datetime.date(2027, 11, 16)
MIERCOLES_17 = datetime.date(2027, 11, 17)
DESPUES_DEL_IV = datetime.date(2028, 1, 10)

A, T, F, J = (
    Asistencia.Estado.ASISTIO,
    Asistencia.Estado.TARDE,
    Asistencia.Estado.FALTO,
    Asistencia.Estado.JUSTIFICADO,
)


@pytest.fixture
def cuarto(anio_abierto):
    return Periodo.objects.create(
        anio_escolar=anio_abierto, numero=4, fecha_inicio=IV_INICIO, fecha_fin=IV_FIN
    )


def tomar(seccion, fecha, marcas, usuario):
    """La jornada de ``fecha`` con ``marcas`` (estudiante → estado), directo en la base."""
    jornada = Jornada.objects.create(seccion=seccion, fecha=fecha, registrado_por=usuario)
    Asistencia.objects.bulk_create(
        Asistencia(jornada=jornada, estudiante=estudiante, estado=estado)
        for estudiante, estado in marcas.items()
    )
    return jornada


def test_dias_de_clase_de_lunes_a_viernes_hasta_la_fecha(cuarto):
    dias = servicios.dias_de_clase(cuarto, HOY_IV)

    assert len(dias) == 11
    assert (dias[0], dias[-1]) == (IV_INICIO, HOY_IV)
    assert all(dia.weekday() < 5 for dia in dias)


def test_dias_de_clase_terminan_con_el_periodo_y_no_empiezan_antes(cuarto):
    dias = servicios.dias_de_clase(cuarto, DESPUES_DEL_IV)

    assert (len(dias), dias[-1]) == (30, IV_FIN)
    assert servicios.dias_de_clase(cuarto, IV_INICIO - datetime.timedelta(days=1)) == []


def test_dias_sin_completar(seccion, docente, cuarto):
    """Sin jornada el 16, incompleta el 17, completas el resto; hoy incompleta no cuenta.

    La retirada el 10, sin marcas desde ese día, no deja días sin completar.
    """
    ana = Estudiante.objects.create(seccion=seccion, apellidos="AAA", nombres="ANA")
    beto = Estudiante.objects.create(seccion=seccion, apellidos="BBB", nombres="BETO")
    retirada = Estudiante.objects.create(
        seccion=seccion,
        apellidos="CCC",
        nombres="CARLA",
        estado=Estudiante.Estado.RETIRADO,
        fecha_estado=datetime.date(2027, 11, 10),
    )
    for dia in servicios.dias_de_clase(cuarto, HOY_IV - datetime.timedelta(days=1)):
        if dia == MARTES_16:
            continue
        marcas = {ana: A} if dia == MIERCOLES_17 else {ana: A, beto: F}
        if dia < datetime.date(2027, 11, 10):
            marcas[retirada] = A
        tomar(seccion, dia, marcas, docente)
    tomar(seccion, HOY_IV, {ana: A}, docente)

    dias = servicios.dias_sin_completar_por_seccion([seccion], cuarto, HOY_IV)

    assert dias == {seccion.pk: 2}


def test_dias_sin_completar_de_un_periodo_terminado(seccion, cuarto):
    """Ya terminó: cuentan sus 30 días hasta el fin; una sección vacía no tiene ninguno."""
    Estudiante.objects.create(seccion=seccion, apellidos="AAA", nombres="ANA")
    vacia = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")

    dias = servicios.dias_sin_completar_por_seccion([seccion, vacia], cuarto, DESPUES_DEL_IV)

    assert dias == {seccion.pk: 30, vacia.pk: 0}


def test_dias_sin_completar_en_dos_consultas(seccion, cuarto, django_assert_num_queries):
    otras = [
        Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=g, nombre="B")
        for g in (3, 4, 5)
    ]
    for s in [seccion, *otras]:
        Estudiante.objects.create(seccion=s, apellidos="AAA", nombres="ANA")

    with django_assert_num_queries(2):
        dias = servicios.dias_sin_completar_por_seccion([seccion, *otras], cuarto, HOY_IV)

    assert set(dias.values()) == {10}


@pytest.fixture
def once_jornadas(seccion, docente, cuarto):
    """Ana: 8 Asistió, 2 Faltó y 1 Justificado en los 11 días; Beto sin marcas; un trasladado
    con 3 Asistió."""
    ana = Estudiante.objects.create(seccion=seccion, apellidos="AAA", nombres="ANA")
    beto = Estudiante.objects.create(seccion=seccion, apellidos="BBB", nombres="BETO")
    trasladado = Estudiante.objects.create(
        seccion=seccion,
        apellidos="TTT",
        nombres="TOMÁS",
        estado=Estudiante.Estado.TRASLADADO,
        fecha_estado=datetime.date(2027, 11, 11),
    )
    estados = [A] * 8 + [F, F, J]
    for n, dia in enumerate(servicios.dias_de_clase(cuarto, HOY_IV)):
        marcas = {ana: estados[n]}
        if n < 3:
            marcas[trasladado] = A
        tomar(seccion, dia, marcas, docente)
    return ana, beto, trasladado


def test_totales_por_estudiante(seccion, cuarto, once_jornadas):
    """Escenario «Totales de un estudiante»: 8, 0, 2, 1 y «72,7 %»; sin marcas, «—»."""
    ana, beto, _ = once_jornadas

    filas = servicios.totales_por_estudiante(seccion, cuarto, HOY_IV)

    assert [fila.estudiante for fila in filas] == [ana, beto]
    de_ana, de_beto = (fila.totales for fila in filas)
    assert (de_ana.asistio, de_ana.tarde, de_ana.falto, de_ana.justificado) == (8, 0, 2, 1)
    assert de_ana.texto_porcentaje == "72,7 %"
    assert de_beto.marcas == 0
    assert de_beto.porcentaje is None
    assert de_beto.texto_porcentaje == "—"


def test_los_totales_de_la_seccion_suman_todas_sus_marcas(seccion, cuarto, once_jornadas):
    """Las marcas del trasladado cuentan en la sección aunque no esté en la tabla (D5)."""
    totales = servicios.totales_de_la_seccion(seccion, cuarto, HOY_IV)

    assert (totales.asistio, totales.tarde, totales.falto, totales.justificado) == (11, 0, 2, 1)
    assert totales.texto_porcentaje == "78,6 %"


def test_los_totales_no_salen_del_periodo(seccion, docente, cuarto):
    ana = Estudiante.objects.create(seccion=seccion, apellidos="AAA", nombres="ANA")
    tomar(seccion, IV_INICIO - datetime.timedelta(days=3), {ana: F}, docente)
    tomar(seccion, IV_INICIO, {ana: A}, docente)

    totales = servicios.totales_de_la_seccion(seccion, cuarto, HOY_IV)

    assert (totales.asistio, totales.falto) == (1, 0)


def test_promedio_ponderado_por_estudiantes():
    """Escenario «Promedio ponderado»: 25 × 90,0 y 15 × 100,0 dan 93,8; sin marcas no entra."""
    promedio = servicios.promedio_ponderado(
        [(25, Decimal("90.0")), (15, Decimal("100.0")), (30, None)]
    )

    assert promedio == Decimal("93.8")
    assert servicios.texto_porcentaje(promedio) == "93,8 %"
    assert servicios.promedio_ponderado([(30, None)]) is None


def test_totales_exactos_con_tres_secciones(seccion, docente, cuarto):
    """Escenario «Totales exactos (RNF-017)»: un periodo completo comparado con las filas."""
    # Un estado distinto por estudiante, día y sección, sin azar: 4 no divide a 7 ni a 3.
    estados = [A, T, F, J]
    secciones = [seccion] + [
        Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=g, nombre="A")
        for g in (3, 4)
    ]
    for s in secciones:
        estudiantes = [
            Estudiante.objects.create(seccion=s, apellidos=f"APELLIDO {n}", nombres="NOMBRE")
            for n in range(6)
        ]
        for d, dia in enumerate(servicios.dias_de_clase(cuarto, IV_FIN)):
            marcas = {e: estados[(7 * n + 3 * d + s.grado) % 4] for n, e in enumerate(estudiantes)}
            tomar(s, dia, marcas, docente)

    por_seccion = servicios.totales_por_seccion(secciones, cuarto, DESPUES_DEL_IV)

    for s in secciones:
        filas = Asistencia.objects.filter(jornada__seccion=s)
        totales = servicios.totales_de_la_seccion(s, cuarto, DESPUES_DEL_IV)
        assert por_seccion[s.pk] == totales
        assert totales.marcas == filas.count() == 30 * 6
        assert totales.asistio == filas.filter(estado=A).count()
        assert totales.tarde == filas.filter(estado=T).count()
        assert totales.falto == filas.filter(estado=F).count()
        assert totales.justificado == filas.filter(estado=J).count()
        de_estudiantes = servicios.totales_por_estudiante(s, cuarto, DESPUES_DEL_IV)
        assert sum(fila.totales.marcas for fila in de_estudiantes) == totales.marcas
