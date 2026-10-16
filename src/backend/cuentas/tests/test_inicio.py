"""Pruebas de la página inicial (spec entorno-desarrollo, requisito "Página inicial")."""

import pytest

DIMENSIONES = [
    "Planificación de sesiones de aprendizaje",
    "Registro y control de notas",
    "Control de asistencia",
]


@pytest.fixture
def respuesta(client):
    return client.get("/")


@pytest.fixture
def html(respuesta):
    return respuesta.content.decode()


def test_pagina_inicial_responde(respuesta):
    assert respuesta.status_code == 200


def test_pagina_inicial_en_espanol_y_adaptada_al_celular(html):
    assert '<html lang="es"' in html
    assert 'name="viewport"' in html


def test_muestra_el_nombre_del_sistema(html):
    assert "CarpetaDocente" in html


def test_muestra_las_tres_dimensiones_en_orden(html):
    posiciones = [html.find(dimension) for dimension in DIMENSIONES]

    assert -1 not in posiciones
    assert posiciones == sorted(posiciones)


@pytest.mark.parametrize(
    "recurso",
    [
        "/static/dist/app.css",
        "/static/dist/vendor/htmx.min.js",
        "/static/dist/vendor/alpine.min.js",
    ],
)
def test_enlaza_estilos_y_scripts_propios(html, recurso):
    assert recurso in html
