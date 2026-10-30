"""Bandera de disponibilidad de cada dimensión (spec pantallas-de-inicio; design de US-001, D7)."""

from dataclasses import replace
from pathlib import Path

from django.template.loader import get_template
from django.urls import NoReverseMatch, reverse

from cuentas.dimensiones import DIMENSIONES, POR_SECCION, tarjeta_inicial

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
    assert [(d.clave, d.titulo, d.subtitulo, d.verbo) for d in DIMENSIONES] == [
        ("sesiones", "Sesiones", "Planificación de sesiones de aprendizaje", "Ver sesiones"),
        ("notas", "Notas", "Registro y control de notas", "Registrar notas"),
        ("asistencia", "Asistencia", "Control de asistencia", "Registrar asistencia"),
    ]


def test_desde_us_030_solo_asistencia_esta_disponible():
    disponibles = [(d.clave, d.url_name) for d in DIMENSIONES if d.disponible or d.url_name]

    assert disponibles == [("asistencia", "asistencia:hoy")]


def test_toda_dimension_disponible_resuelve_su_pantalla():
    """Escenario "Bandera activa sin pantalla": falla antes de que el cambio se fusione."""
    assert sin_pantalla(DIMENSIONES) == []


def test_la_revision_detecta_una_bandera_activa_sin_pantalla():
    sesiones = DIMENSIONES[0]

    assert sin_pantalla([replace(sesiones, disponible=True, url_name=None)]) == ["sesiones"]
    assert sin_pantalla([replace(sesiones, disponible=True, url_name="no:existe")]) == ["sesiones"]
    assert sin_pantalla([replace(sesiones, disponible=True, url_name="docente:portada")]) == []


def test_cada_dimension_tiene_su_icono_y_su_miniatura():
    for dimension in DIMENSIONES:
        assert (CARPETA_PLANTILLAS / "iconos" / f"{dimension.icono}.svg").is_file()
        get_template(f"componentes/miniatura_{dimension.clave}.html")


# --- Tarjeta inicial del carrusel ---


def test_sin_ninguna_disponible_abre_en_la_primera():
    sin_disponibles = [replace(d, disponible=False) for d in DIMENSIONES]

    assert tarjeta_inicial(sin_disponibles) == "sesiones"


def test_abre_en_la_primera_disponible_en_el_orden_de_las_tarjetas():
    sesiones, notas, asistencia = DIMENSIONES
    solo_asistencia = (sesiones, notas, replace(asistencia, disponible=True))
    notas_y_asistencia = (
        sesiones,
        replace(notas, disponible=True),
        replace(asistencia, disponible=True),
    )

    assert tarjeta_inicial(solo_asistencia) == "asistencia"
    assert tarjeta_inicial(notas_y_asistencia) == "notas"
