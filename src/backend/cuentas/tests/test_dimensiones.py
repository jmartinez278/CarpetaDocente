"""Bandera de disponibilidad de cada dimensión (spec pantallas-de-inicio; design de US-001, D7)."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.template.loader import get_template
from django.urls import NoReverseMatch, reverse

from cuentas.dimensiones import DIMENSIONES, POR_SECCION, navegacion_docente

CARPETA_PLANTILLAS = Path(__file__).resolve().parents[2] / "templates"


def sin_pantalla(dimensiones):
    """Claves de las dimensiones disponibles cuyo ``url_name`` no resuelve una ruta."""
    faltan = []
    for dimension in dimensiones:
        if not dimension.disponible:
            continue
        # Una ruta de la sección (Asistencia) necesita su id; cualquiera sirve para resolverla.
        argumentos = [1] if dimension.clave in POR_SECCION else []
        try:
            reverse(dimension.url_name, args=argumentos)
        except NoReverseMatch:
            faltan.append(dimension.clave)
    return faltan


def test_las_tres_dimensiones_en_orden_con_sus_textos():
    """Escenario «Portada al entrar»: orden Asistencia, Sesiones y Notas, con su frase
    (rebrand-portada, D2)."""
    assert [(d.clave, d.titulo, d.frase, d.verbo) for d in DIMENSIONES] == [
        (
            "asistencia",
            "Asistencia",
            "Marca la asistencia de cada día.",
            "Registrar asistencia",
        ),
        (
            "sesiones",
            "Sesiones",
            "Envía tu sesión a la dirección y compártela con tus colegas.",
            "Ver sesiones",
        ),
        (
            "notas",
            "Notas",
            "Registra tus notas por competencia para el SIAGIE.",
            "Registrar notas",
        ),
    ]


def test_las_tarjetas_no_traen_el_subtitulo_formal():
    assert not hasattr(DIMENSIONES[0], "subtitulo")


def test_desde_us_020_notas_y_asistencia_estan_disponibles():
    disponibles = [(d.clave, d.url_name) for d in DIMENSIONES if d.disponible or d.url_name]

    assert disponibles == [("asistencia", "asistencia:hoy"), ("notas", "notas:hoja")]


def test_notas_y_asistencia_son_pantallas_de_la_seccion():
    assert {"notas", "asistencia"} <= POR_SECCION


def test_toda_dimension_disponible_resuelve_su_pantalla():
    """Escenario "Bandera activa sin pantalla": falla antes de que el cambio se fusione."""
    assert sin_pantalla(DIMENSIONES) == []


def test_la_revision_detecta_una_bandera_activa_sin_pantalla():
    sesiones = next(d for d in DIMENSIONES if d.clave == "sesiones")

    assert sin_pantalla([replace(sesiones, disponible=True, url_name=None)]) == ["sesiones"]
    assert sin_pantalla([replace(sesiones, disponible=True, url_name="no:existe")]) == ["sesiones"]
    assert sin_pantalla([replace(sesiones, disponible=True, url_name="docente:portada")]) == []


def test_cada_dimension_tiene_su_icono_y_su_miniatura():
    for dimension in DIMENSIONES:
        assert (CARPETA_PLANTILLAS / "iconos" / f"{dimension.icono}.svg").is_file()
        get_template(f"rb/miniatura_{dimension.clave}.html")


def test_sin_carrusel_no_hay_tarjeta_inicial():
    import cuentas.dimensiones as modulo

    assert not hasattr(modulo, "tarjeta_inicial")


# --- Destinos del ☰ (spec pantallas-de-inicio, «Navegación de la docente»; rebrand-base, D6) ---

SECCION = SimpleNamespace(pk=7)


def destinos(seccion=SECCION, vista=None, dimensiones=DIMENSIONES):
    return navegacion_docente(seccion, vista, dimensiones)


def test_inicio_y_las_tres_dimensiones_en_el_orden_del_menu():
    assert [(d.clave, d.titulo) for d in destinos()] == [
        ("inicio", "Inicio"),
        ("sesiones", "Sesiones"),
        ("asistencia", "Asistencia"),
        ("notas", "Notas"),
    ]


def test_cada_destino_tiene_su_icono():
    for destino in destinos():
        assert (CARPETA_PLANTILLAS / "iconos" / f"{destino.icono}.svg").is_file()


def test_con_seccion_unica_enlaza_igual_que_las_tarjetas():
    """Escenario «Abrir el ☰»."""
    urls = {d.clave: d.url for d in destinos()}

    assert urls == {
        "inicio": reverse("docente:portada"),
        "sesiones": None,
        "asistencia": reverse("asistencia:hoy", args=[7]),
        "notas": reverse("notas:hoja", args=[7]),
    }


def test_sin_seccion_unica_solo_inicio_enlaza():
    """Escenario «Destino no disponible»: lo no disponible sigue en la lista, sin enlace."""
    urls = {d.clave: d.url for d in destinos(seccion=None)}

    assert urls == {
        "inicio": reverse("docente:portada"),
        "sesiones": None,
        "asistencia": None,
        "notas": None,
    }


def test_sesiones_disponible_enlaza_su_pantalla():
    con_sesiones = tuple(
        replace(d, disponible=True, url_name="sesiones:inicio") if d.clave == "sesiones" else d
        for d in DIMENSIONES
    )

    assert destinos(dimensiones=con_sesiones)[1].url == reverse("sesiones:inicio")


@pytest.mark.parametrize(
    ("vista", "actual"),
    [
        ("docente:portada", "inicio"),
        ("notas:hoja", "notas"),
        ("competencias:pantalla", "notas"),
        ("asistencia:hoy", "asistencia"),
        ("asistencia:restantes", "asistencia"),
        ("docente:sin_permiso", None),
        ("estudiantes:lista", None),
        (None, None),
    ],
)
def test_ubicacion_actual(vista, actual):
    """Escenario «Ubicación actual»: a lo más un destino marcado."""
    marcados = [d.clave for d in destinos(vista=vista) if d.actual]

    assert marcados == ([actual] if actual else [])


def test_un_destino_no_disponible_no_es_el_actual():
    assert not any(d.actual for d in destinos(seccion=None, vista="notas:hoja"))
    assert not any(d.actual for d in destinos(vista="sesiones:inicio"))
