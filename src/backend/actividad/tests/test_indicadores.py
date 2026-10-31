"""Indicadores por semana: KPI-01 y jornadas registradas, sin la demostración (D9).

Las entradas se crean con ``registrar`` y una ``fecha_hora`` fija. Las semanas de prueba son de
2027 (el año ABIERTO de las fixtures): el lunes 1 y el lunes 8 de marzo.
"""

from datetime import UTC, date, datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from actividad.models import Operacion
from actividad.servicios import indicadores_por_semana, rango_por_defecto, texto_activos
from actividad.tests.test_panel import URL_LISTA, entrada
from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.django_db

URL_INDICADORES = "admin:actividad_registroactividad_indicadores"
LUNES_1 = date(2027, 3, 1)
LUNES_8 = date(2027, 3, 8)
MARTES_2 = datetime(2027, 3, 2, 15, 0, tzinfo=UTC)
JUEVES_4 = datetime(2027, 3, 4, 15, 0, tzinfo=UTC)


@pytest.fixture
def con_seccion(anio_abierto):
    """Da a una cuenta Docente una sección del año ABIERTO (la crea con un nombre libre)."""
    nombres = iter("BCDEFGHIJK")

    def dar(usuario, anio=anio_abierto):
        Seccion.objects.create(anio_escolar=anio, grado=1, nombre=next(nombres), docente=usuario)
        return usuario

    return dar


@pytest.fixture
def participante(docente, con_seccion):
    return con_seccion(docente)


def semana(desde=LUNES_1, hasta=None):
    filas = indicadores_por_semana(desde, hasta or desde)
    assert len(filas) == 1
    return filas[0]


# --- Semanas ---------------------------------------------------------------------------------


def test_semanas_de_lunes_a_domingo_todas_con_cero_si_no_hay_actividad():
    filas = indicadores_por_semana(date(2027, 3, 3), date(2027, 3, 10))

    assert [(f["lunes"], f["domingo"]) for f in filas] == [
        (LUNES_1, date(2027, 3, 7)),
        (LUNES_8, date(2027, 3, 14)),
    ]
    assert all(f["jornadas"] == 0 and f["activos"] == 0 for f in filas)


def test_el_domingo_a_las_23_30_de_lima_cuenta_en_su_semana(participante):
    # Domingo 7 a las 23:30 de Lima son las 04:30 UTC del lunes 8.
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, datetime(2027, 3, 8, 4, 30, tzinfo=UTC))

    primera, segunda = indicadores_por_semana(LUNES_1, LUNES_8)

    assert (primera["jornadas"], primera["activos"]) == (1, 1)
    assert (segunda["jornadas"], segunda["activos"]) == (0, 0)


def test_un_rango_que_corta_una_semana_la_muestra_entera(participante):
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, MARTES_2)

    # Del jueves 4 al viernes 5: la semana entera, con lo del martes.
    fila = semana(date(2027, 3, 4), date(2027, 3, 5))

    assert (fila["lunes"], fila["jornadas"]) == (LUNES_1, 1)


def test_rango_por_defecto_del_1_de_enero_del_anio_abierto_a_hoy(anio_abierto):
    assert rango_por_defecto(date(2027, 3, 10)) == (date(2027, 1, 1), date(2027, 3, 10))


def test_rango_por_defecto_con_dos_anios_abiertos_toma_el_mas_reciente(
    anio_abierto, otra_institucion
):
    AnioEscolar.objects.create(institucion=otra_institucion, anio=2028)

    assert rango_por_defecto(date(2028, 5, 2)) == (date(2028, 1, 1), date(2028, 5, 2))


def test_rango_por_defecto_sin_anio_abierto_es_el_anio_en_curso(db):
    assert rango_por_defecto(date(2027, 3, 10)) == (date(2027, 1, 1), date(2027, 3, 10))


def test_rango_por_defecto_con_el_anio_abierto_aun_por_empezar_es_el_anio_en_curso(
    anio_abierto,
):
    # Año 2027 abierto en octubre de 2026: el 1 de enero de 2027 quedaría después de hoy.
    assert rango_por_defecto(date(2026, 10, 30)) == (date(2026, 1, 1), date(2026, 10, 30))


# --- Participantes ---------------------------------------------------------------------------


def test_participantes_solo_docentes_activas_reales_con_seccion_en_anio_abierto(
    participante, crear_usuario, con_seccion, institucion
):
    # Dos secciones de la misma docente cuentan una vez.
    con_seccion(participante)
    desactivada = con_seccion(crear_usuario("dquispe"))
    desactivada.is_active = False
    desactivada.save()
    crear_usuario("ssinseccion")
    cerrado = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    con_seccion(crear_usuario("cpasado"), anio=cerrado)
    con_seccion(crear_usuario("demo.docente1", es_demo=True))

    assert semana()["participantes"] == 1


# --- Docentes activos (KPI-01) ---------------------------------------------------------------


def test_solo_iniciar_y_cerrar_sesion_no_cuenta_como_activa(participante):
    entrada(participante, Operacion.INICIO_SESION, MARTES_2)
    entrada(participante, Operacion.CIERRE_SESION, MARTES_2)

    assert semana()["activos"] == 0


def test_asistencia_dos_dias_de_la_semana_cuenta_una_vez(participante):
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, MARTES_2)
    entrada(participante, Operacion.ASISTENCIA_CAMBIADA, MARTES_2)
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, JUEVES_4)

    assert semana()["activos"] == 1


def test_quien_no_es_participante_no_cuenta_como_activa(crear_usuario):
    entrada(crear_usuario("ssinseccion"), Operacion.ASISTENCIA_CAMBIADA, MARTES_2)

    assert semana()["activos"] == 0


def test_tres_de_cinco_se_muestra_con_su_porcentaje(crear_usuario, con_seccion):
    docentes = [con_seccion(crear_usuario(f"docente{n}")) for n in range(5)]
    for docente in docentes[:3]:
        entrada(docente, Operacion.ASISTENCIA_CAMBIADA, JUEVES_4)

    fila = semana()

    assert (fila["activos"], fila["participantes"]) == (3, 5)
    assert fila["activos_texto"] == "3 / 5 (60 %)"


@pytest.mark.parametrize(
    ("activos", "participantes", "texto"),
    [(3, 5, "3 / 5 (60 %)"), (0, 0, "0 / 0 (—)"), (1, 3, "1 / 3 (33 %)"), (2, 3, "2 / 3 (67 %)")],
)
def test_texto_de_activos(activos, participantes, texto):
    assert texto_activos(activos, participantes) == texto


def test_sin_participantes_se_muestra_cero_de_cero():
    assert semana()["activos_texto"] == "0 / 0 (—)"


# --- Jornadas y la demostración --------------------------------------------------------------


def test_jornadas_cuentan_registro_asistencia_sin_demo_ni_usuario_vacio(
    participante, crear_usuario, con_seccion
):
    demo = con_seccion(crear_usuario("demo.docente1", es_demo=True))
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, MARTES_2)
    entrada(participante, Operacion.ASISTENCIA_CAMBIADA, MARTES_2)
    entrada(demo, Operacion.REGISTRO_ASISTENCIA, MARTES_2)
    entrada(None, Operacion.REGISTRO_ASISTENCIA, MARTES_2)

    assert semana()["jornadas"] == 1


def test_demo_cargada_no_cuenta(participante, crear_usuario, con_seccion):
    for n in (1, 2):
        demo = con_seccion(crear_usuario(f"demo.docente{n}", es_demo=True))
        entrada(demo, Operacion.REGISTRO_ASISTENCIA, MARTES_2)
        entrada(demo, Operacion.ASISTENCIA_CAMBIADA, MARTES_2)
        entrada(demo, Operacion.JORNADA_COMPLETA, MARTES_2)
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, JUEVES_4)

    fila = semana()

    assert (fila["activos_texto"], fila["jornadas"]) == ("1 / 1 (100 %)", 1)


def test_sesiones_y_secciones_con_notas_quedan_sin_dato():
    fila = semana()

    assert (fila["sesiones"], fila["secciones_con_notas"]) == (None, None)


# --- Página del panel ------------------------------------------------------------------------


@pytest.fixture
def panel(client, administrador):
    client.force_login(administrador)
    return client


def test_la_pagina_muestra_las_semanas_del_rango_elegido(panel, participante):
    entrada(participante, Operacion.REGISTRO_ASISTENCIA, MARTES_2)

    respuesta = panel.get(reverse(URL_INDICADORES), {"desde": "2027-03-01", "hasta": "2027-03-14"})

    assert respuesta.status_code == 200
    assert len(respuesta.context["filas"]) == 2
    html = respuesta.content.decode()
    assert "Indicadores por semana" in html
    assert "1 / 1 (100 %)" in html
    for encabezado in (
        "Semana",
        "Docentes activos / participantes",
        "Jornadas registradas",
        "Sesiones cargadas",
        "Secciones con notas",
    ):
        assert f'<th scope="col">{encabezado}</th>' in html
    # "—" en las dos columnas sin dato de cada fila.
    assert html.count("<td>—</td>") == 4
    for campo in ("desde", "hasta"):
        assert f'for="id_{campo}"' in html


def test_la_pagina_sin_fechas_usa_el_rango_por_defecto(panel):
    respuesta = panel.get(reverse(URL_INDICADORES))

    assert respuesta.status_code == 200
    filas = respuesta.context["filas"]
    assert filas
    hoy = timezone.localdate()
    assert filas[-1]["domingo"] >= hoy >= filas[-1]["lunes"]


def test_la_pagina_sin_fechas_muestra_el_rango_en_sus_campos(panel):
    # Un <input type="date"> solo acepta AAAA-MM-DD; con "01/01/2026" el campo se ve vacío.
    desde, hasta = rango_por_defecto(timezone.localdate())

    html = panel.get(reverse(URL_INDICADORES)).content.decode()

    assert f'value="{desde.isoformat()}"' in html
    assert f'value="{hasta.isoformat()}"' in html


def test_rango_al_reves_muestra_su_mensaje_y_ninguna_fila(panel):
    respuesta = panel.get(reverse(URL_INDICADORES), {"desde": "2027-03-14", "hasta": "2027-03-01"})

    assert respuesta.status_code == 200
    assert respuesta.context["filas"] == []
    assert "La fecha de inicio debe ser anterior a la de fin" in respuesta.content.decode()


def test_la_lista_del_registro_enlaza_a_los_indicadores(panel):
    respuesta = panel.get(reverse(URL_LISTA))

    assert f'href="{reverse(URL_INDICADORES)}"' in respuesta.content.decode()
