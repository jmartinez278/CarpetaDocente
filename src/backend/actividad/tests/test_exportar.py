"""Exportar el registro filtrado a CSV desde el panel (D10)."""

import csv
import io
from datetime import UTC, datetime

import pytest
from django.urls import reverse

from actividad.models import Operacion, RegistroActividad
from actividad.servicios import celda_segura
from actividad.tests.conftest import entrar
from actividad.tests.test_panel import URL_LISTA, entrada

pytestmark = pytest.mark.django_db

URL_EXPORTAR = "admin:actividad_registroactividad_exportar"
BOM = "﻿"
COLUMNAS = ["Fecha y hora", "Usuario", "Operación", "Entidad", "Identificador", "Detalle"]


@pytest.fixture
def panel(client, administrador):
    entrar(client, administrador)
    return client


@pytest.fixture
def entradas(docente):
    return {
        # 03:30:15 UTC del 26-10 son las 22:30:15 del 25-10 en Lima.
        "cambio": entrada(
            docente,
            Operacion.ASISTENCIA_CAMBIADA,
            datetime(2026, 10, 26, 3, 30, 15, tzinfo=UTC),
            entidad="asistencia",
            entidad_id=12,
            detalle={"estudiante": 5, "anterior": None, "nuevo": "P", "origen": "toque"},
        ),
        "inicio": entrada(
            docente, Operacion.INICIO_SESION, datetime(2026, 10, 26, 13, 0, tzinfo=UTC)
        ),
        "consola": entrada(
            None, Operacion.ASISTENCIA_CAMBIADA, datetime(2026, 10, 27, 13, 0, tzinfo=UTC)
        ),
    }


def exportar(cliente, filtros=""):
    return cliente.post(reverse(URL_EXPORTAR) + filtros)


def filas_del_csv(respuesta):
    texto = respuesta.content.decode("utf-8")
    assert texto.startswith(BOM)
    return list(csv.reader(io.StringIO(texto.removeprefix(BOM))))


def test_con_un_filtro_trae_solo_esas_filas_con_bom_columnas_y_hora_de_lima(
    panel, docente, entradas
):
    respuesta = exportar(panel, f"?operacion__exact={Operacion.ASISTENCIA_CAMBIADA}")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "text/csv; charset=utf-8"
    assert respuesta["Content-Disposition"].startswith("attachment; filename=")
    filas = filas_del_csv(respuesta)
    assert filas[0] == COLUMNAS
    # En el orden de la lista: de la más reciente a la más antigua.
    assert filas[1] == ["27-10-2026 08:00:00", "", "ASISTENCIA_CAMBIADA", "", "", "{}"]
    assert filas[2][:5] == [
        "25-10-2026 22:30:15",
        docente.username,
        "ASISTENCIA_CAMBIADA",
        "asistencia",
        "12",
    ]
    assert '"estudiante": 5' in filas[2][5]
    assert len(filas) == 3


def test_sin_filtros_trae_todo_el_registro(panel, entradas):
    filas = filas_del_csv(exportar(panel))

    assert len(filas) == 1 + len(entradas)


def test_deja_registro_exportado_con_filtros_y_numero_de_filas(panel, administrador, entradas):
    exportar(panel, f"?operacion__exact={Operacion.ASISTENCIA_CAMBIADA}")

    registro = RegistroActividad.objects.get(operacion=Operacion.REGISTRO_EXPORTADO)
    assert registro.usuario == administrador
    assert registro.detalle == {
        "filtros": {"operacion__exact": "ASISTENCIA_CAMBIADA"},
        "filas": 2,
    }


def test_la_exportacion_no_se_incluye_a_si_misma(panel, entradas):
    exportar(panel)
    filas = filas_del_csv(exportar(panel))

    # Trae la primera exportación, no la que está en curso.
    assert [fila[2] for fila in filas[1:]].count("REGISTRO_EXPORTADO") == 1


def test_get_responde_405_y_no_deja_entrada(panel, entradas):
    respuesta = panel.get(reverse(URL_EXPORTAR))

    assert respuesta.status_code == 405
    assert not RegistroActividad.objects.filter(operacion=Operacion.REGISTRO_EXPORTADO).exists()


@pytest.mark.parametrize("rol", ["docente", "direccion"])
def test_otro_rol_no_obtiene_el_csv(client, request, entradas, rol):
    entrar(client, request.getfixturevalue(rol))

    respuesta = exportar(client)

    assert respuesta.status_code in (302, 403)
    assert "text/csv" not in respuesta.get("Content-Type", "")
    assert not RegistroActividad.objects.filter(operacion=Operacion.REGISTRO_EXPORTADO).exists()


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("=HYPERLINK()", "'=HYPERLINK()"),
        ("+1", "'+1"),
        ("-1", "'-1"),
        ("@SUM(A1)", "'@SUM(A1)"),
        (" =1+1", "' =1+1"),
        ("\t=1", "'\t=1"),
        ("aquispe", "aquispe"),
        ("", ""),
        ("12", "12"),
    ],
)
def test_celda_que_parece_formula_sale_con_apostrofo(valor, esperado):
    assert celda_segura(valor) == esperado


def test_el_csv_escapa_las_celdas_peligrosas(panel, docente):
    entrada(
        docente,
        Operacion.ESTUDIANTE_EDITADO,
        datetime(2026, 10, 26, 13, 0, tzinfo=UTC),
        entidad="=cmd",
        entidad_id="-5",
    )

    fila = filas_del_csv(exportar(panel))[1]

    assert fila[3:5] == ["'=cmd", "'-5"]


def test_la_lista_tiene_el_boton_exportar_con_los_filtros_puestos(panel, entradas):
    respuesta = panel.get(reverse(URL_LISTA), {"operacion__exact": "INICIO_SESION"})

    html = respuesta.content.decode()
    assert f'action="{reverse(URL_EXPORTAR)}?operacion__exact=INICIO_SESION"' in html
    assert 'method="post"' in html
    assert "Exportar CSV" in html
