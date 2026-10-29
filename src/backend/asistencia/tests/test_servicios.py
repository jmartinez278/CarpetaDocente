"""Pruebas de los servicios de asistencia (spec asistencia-jornada; design de US-030, D2).

Todas fijan ``hoy``: ninguna depende del reloj. El 28-10-2026 es miércoles.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from asistencia import servicios
from asistencia.models import Asistencia, Jornada
from institucion.models import Estudiante, Seccion

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 10, 28)
SABADO = datetime.date(2026, 10, 31)
AYER = HOY - datetime.timedelta(days=1)
MANANA = HOY + datetime.timedelta(days=1)


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


def marcar(seccion, estudiante, estado, docente, nota="", fecha=HOY, hoy=HOY):
    return servicios.marcar(seccion, estudiante.pk, fecha, estado, nota, docente, hoy=hoy)


def restantes(seccion, estudiantes, docente, fecha=HOY, hoy=HOY):
    return servicios.marcar_restantes(seccion, [e.pk for e in estudiantes], fecha, docente, hoy=hoy)


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


@pytest.mark.parametrize("fecha", [AYER, MANANA])
def test_fecha_que_no_es_hoy_se_rechaza_sin_crear_jornada(seccion, lista, docente, fecha):
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


def test_marcar_restantes_rechaza_una_fecha_que_no_es_hoy(seccion, lista, docente):
    with pytest.raises(servicios.FechaNoValida):
        restantes(seccion, lista, docente, fecha=AYER)

    assert Jornada.objects.count() == 0


def test_marcar_restantes_sin_ids_no_crea_jornada(seccion, lista, docente):
    restantes(seccion, [], docente)

    assert Jornada.objects.count() == 0


# --- lista_de_hoy ---


def test_lista_de_hoy_sin_jornada_no_la_crea(seccion, lista):
    datos = servicios.lista_de_hoy(seccion, hoy=HOY)

    assert Jornada.objects.count() == 0
    assert datos.jornada is None
    assert (datos.marcados, datos.total, datos.sin_marcar) == (0, 5, 5)
    assert not datos.completa
    assert [f.estado for f in datos.filas] == [None] * 5


def test_lista_de_hoy_ordena_y_numera_de_1_a_m_solo_los_activos(seccion, lista):
    Estudiante.objects.filter(pk=lista[1].pk).update(estado="TRASLADADO")
    Estudiante.objects.filter(pk=lista[3].pk).update(estado="RETIRADO")

    datos = servicios.lista_de_hoy(seccion, hoy=HOY)

    assert [(f.numero, f.estudiante.apellidos) for f in datos.filas] == [
        (1, "AAA"),
        (2, "CCC"),
        (3, "EEE"),
    ]
    assert [e.apellidos for e in datos.no_activos] == ["BBB", "DDD"]
    assert datos.total == 3


def test_lista_de_hoy_cuenta_el_avance_y_los_totales(seccion, lista, docente):
    marcar(seccion, lista[0], "ASISTIO", docente)
    marcar(seccion, lista[1], "ASISTIO", docente)
    marcar(seccion, lista[2], "TARDE", docente)
    marcar(seccion, lista[3], "JUSTIFICADO", docente, nota="Cita")

    datos = servicios.lista_de_hoy(seccion, hoy=HOY)

    assert (datos.marcados, datos.total, datos.sin_marcar) == (4, 5, 1)
    assert datos.totales == {"ASISTIO": 2, "TARDE": 1, "FALTO": 0, "JUSTIFICADO": 1}
    assert datos.filas[3].nota == "Cita"
    assert datos.filas[4].estado is None
    assert not datos.completa


def test_lista_de_hoy_es_completa_cuando_los_activos_tienen_estado(seccion, lista, docente):
    Estudiante.objects.filter(pk=lista[4].pk).update(estado="RETIRADO")
    for estudiante in lista[:4]:
        marcar(seccion, estudiante, "ASISTIO", docente)

    datos = servicios.lista_de_hoy(seccion, hoy=HOY)

    assert datos.completa
    assert datos.sin_marcar == 0


def test_lista_de_hoy_hace_tres_consultas(seccion, lista, docente, django_assert_num_queries):
    marcar(seccion, lista[0], "ASISTIO", docente)

    with django_assert_num_queries(3):  # jornada, estudiantes y asistencias
        servicios.lista_de_hoy(seccion, hoy=HOY)


def test_lista_de_hoy_de_otra_fecha_no_mezcla_jornadas(seccion, lista, docente):
    marcar(seccion, lista[0], "ASISTIO", docente)

    datos = servicios.lista_de_hoy(seccion, hoy=MANANA)

    assert datos.jornada is None
    assert datos.marcados == 0


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
