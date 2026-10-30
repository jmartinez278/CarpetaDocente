"""La asistencia en el registro de actividad (design de US-008, D6).

Escenarios "Camino ideal", "Primer toque del día", "Mismo estado otra vez", "Lote", "Jornada
completa", "Justificación" y "La operación falla" del spec registro-actividad. Todas fijan ``hoy``:
el 28-10-2026 es miércoles.
"""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from asistencia import servicios
from asistencia.models import Asistencia, Jornada
from institucion.models import Estudiante, Seccion

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 10, 28)
AYER = HOY - datetime.timedelta(days=1)
A = Asistencia.Estado


@pytest.fixture
def lista(seccion):
    """Tres estudiantes activos, ya en orden alfabético."""
    nombres = [("AAA", "ANA"), ("BBB", "BETO"), ("CCC", "CARLA")]
    return [Estudiante.objects.create(seccion=seccion, apellidos=a, nombres=n) for a, n in nombres]


def marcar(seccion, estudiante, estado, docente, nota="", fecha=HOY):
    servicios.marcar(seccion, estudiante.pk, fecha, estado, nota, docente, hoy=HOY)


def restantes(seccion, estudiantes, docente):
    servicios.marcar_restantes(seccion, [e.pk for e in estudiantes], HOY, docente, hoy=HOY)


def entradas(operacion=None):
    consulta = RegistroActividad.objects.order_by("id")
    if operacion:
        consulta = consulta.filter(operacion=operacion)
    return list(consulta)


def cambios():
    return [e.detalle for e in entradas(Operacion.ASISTENCIA_CAMBIADA)]


# --- Camino ideal y primer toque ---


def test_primer_toque_deja_registro_asistencia_y_asistencia_cambiada(seccion, lista, docente):
    marcar(seccion, lista[0], A.ASISTIO, docente)

    jornada = Jornada.objects.get()
    registro, cambio = entradas()
    assert registro.operacion == Operacion.REGISTRO_ASISTENCIA
    assert registro.usuario == docente
    assert (registro.entidad, registro.entidad_id) == ("jornada", str(jornada.pk))
    assert registro.detalle == {"seccion": seccion.pk, "fecha": "2026-10-28"}
    assert registro.fecha_hora is not None
    assert cambio.operacion == Operacion.ASISTENCIA_CAMBIADA
    assert cambio.usuario == docente
    assert (cambio.entidad, cambio.entidad_id) == ("asistencia", str(jornada.pk))
    assert cambio.detalle == {
        "estudiante": lista[0].pk,
        "anterior": None,
        "nuevo": A.ASISTIO,
        "nota_cambiada": False,
        "origen": "toque",
    }


def test_el_segundo_toque_no_deja_otro_registro_asistencia(seccion, lista, docente):
    marcar(seccion, lista[0], A.ASISTIO, docente)
    marcar(seccion, lista[1], A.ASISTIO, docente)

    assert len(entradas(Operacion.REGISTRO_ASISTENCIA)) == 1


def test_cambio_de_estado_dice_el_anterior_y_el_nuevo(seccion, lista, docente):
    marcar(seccion, lista[0], A.ASISTIO, docente)
    marcar(seccion, lista[0], A.FALTO, docente)

    assert cambios()[-1] == {
        "estudiante": lista[0].pk,
        "anterior": A.ASISTIO,
        "nuevo": A.FALTO,
        "nota_cambiada": False,
        "origen": "toque",
    }


# --- Mismo estado otra vez y justificación ---


def test_mismo_estado_y_nota_otra_vez_no_deja_entrada(seccion, lista, docente):
    marcar(seccion, lista[0], A.JUSTIFICADO, docente, nota="Cita médica")
    antes = len(entradas())

    marcar(seccion, lista[0], A.JUSTIFICADO, docente, nota="Cita médica")

    assert len(entradas()) == antes


def test_nota_cambiada_lo_dice_sin_el_texto(seccion, lista, docente):
    marcar(seccion, lista[0], A.JUSTIFICADO, docente, nota="Cita médica")
    marcar(seccion, lista[0], A.JUSTIFICADO, docente, nota="Viaje familiar")

    ultimo = entradas(Operacion.ASISTENCIA_CAMBIADA)[-1]
    assert ultimo.detalle == {
        "estudiante": lista[0].pk,
        "anterior": A.JUSTIFICADO,
        "nuevo": A.JUSTIFICADO,
        "nota_cambiada": True,
        "origen": "toque",
    }
    for entrada in entradas():
        texto = str(entrada.detalle)
        assert "Cita médica" not in texto
        assert "Viaje familiar" not in texto


def test_la_primera_justificacion_con_nota_dice_nota_cambiada(seccion, lista, docente):
    marcar(seccion, lista[0], A.JUSTIFICADO, docente, nota="Cita médica")

    assert cambios()[-1]["nota_cambiada"] is True


# --- Lote ---


def test_lote_deja_una_entrada_por_cada_sin_marcar_con_origen_lote(seccion, lista, docente):
    marcar(seccion, lista[0], A.FALTO, docente)

    restantes(seccion, lista, docente)

    del_lote = [c for c in cambios() if c["origen"] == "lote"]
    assert sorted(c["estudiante"] for c in del_lote) == sorted([lista[1].pk, lista[2].pk])
    for cambio in del_lote:
        assert cambio["anterior"] is None
        assert cambio["nuevo"] == A.ASISTIO
        assert cambio["nota_cambiada"] is False
    assert all(e.usuario == docente for e in entradas(Operacion.ASISTENCIA_CAMBIADA))


def test_lote_que_abre_la_jornada_deja_registro_asistencia(seccion, lista, docente):
    restantes(seccion, lista, docente)

    assert len(entradas(Operacion.REGISTRO_ASISTENCIA)) == 1
    assert len(cambios()) == 3


def test_lote_repetido_no_deja_entradas_nuevas(seccion, lista, docente):
    restantes(seccion, lista, docente)
    antes = len(entradas())

    restantes(seccion, lista, docente)

    assert len(entradas()) == antes


# --- Jornada completa ---


def test_jornada_completa_al_marcar_al_ultimo_activo(seccion, lista, docente):
    marcar(seccion, lista[0], A.ASISTIO, docente)
    marcar(seccion, lista[1], A.ASISTIO, docente)
    assert entradas(Operacion.JORNADA_COMPLETA) == []

    marcar(seccion, lista[2], A.TARDE, docente)

    (completa,) = entradas(Operacion.JORNADA_COMPLETA)
    jornada = Jornada.objects.get()
    assert (completa.entidad, completa.entidad_id) == ("jornada", str(jornada.pk))
    assert completa.usuario == docente


def test_jornada_completa_una_sola_vez_aunque_luego_cambie_un_estado(seccion, lista, docente):
    for estudiante in lista:
        marcar(seccion, estudiante, A.ASISTIO, docente)

    marcar(seccion, lista[0], A.FALTO, docente)
    restantes(seccion, lista, docente)

    assert len(entradas(Operacion.JORNADA_COMPLETA)) == 1


def test_jornada_completa_cuando_el_lote_marca_al_ultimo(seccion, lista, docente):
    marcar(seccion, lista[0], A.ASISTIO, docente)

    restantes(seccion, lista, docente)

    assert len(entradas(Operacion.JORNADA_COMPLETA)) == 1
    assert entradas()[-1].operacion == Operacion.JORNADA_COMPLETA


def test_un_estudiante_no_activo_no_impide_la_jornada_completa(seccion, lista, docente):
    lista[2].estado = Estudiante.Estado.RETIRADO
    lista[2].save()

    marcar(seccion, lista[0], A.ASISTIO, docente)
    marcar(seccion, lista[1], A.ASISTIO, docente)

    assert len(entradas(Operacion.JORNADA_COMPLETA)) == 1


# --- La operación falla: sin entrada ---


def test_toque_de_otra_seccion_no_deja_entrada(seccion, lista, docente):
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")
    ajeno = Estudiante.objects.create(seccion=otra, apellidos="ZZZ", nombres="ZOE")

    with pytest.raises(Estudiante.DoesNotExist):
        marcar(seccion, ajeno, A.ASISTIO, docente)

    assert entradas() == []


def test_toque_con_fecha_que_no_es_hoy_no_deja_entrada(seccion, lista, docente):
    with pytest.raises(servicios.FechaNoValida):
        marcar(seccion, lista[0], A.ASISTIO, docente, fecha=AYER)

    assert entradas() == []


def test_si_falla_el_guardado_no_queda_entrada(seccion, lista, docente, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("base caída")

    monkeypatch.setattr(Asistencia.objects, "bulk_create", falla)

    with pytest.raises(RuntimeError):
        marcar(seccion, lista[0], A.ASISTIO, docente)

    assert entradas() == []
    assert not Jornada.objects.exists()


# --- Una lectura no deja entrada ---


def test_abrir_la_asistencia_de_hoy_no_deja_entrada(client, seccion, lista, docente, monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: HOY)
    seccion.docente = docente
    seccion.save()
    client.force_login(docente)
    antes = len(entradas())

    respuesta = client.get(reverse("asistencia:hoy", args=[seccion.pk]))

    assert respuesta.status_code == 200
    assert len(entradas()) == antes


def test_si_falla_el_registro_el_toque_no_se_guarda(seccion, lista, docente, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("registro caído")

    monkeypatch.setattr(servicios, "registrar", falla)

    with pytest.raises(RuntimeError):
        marcar(seccion, lista[0], A.ASISTIO, docente)

    assert not Jornada.objects.exists()
    assert not Asistencia.objects.exists()
