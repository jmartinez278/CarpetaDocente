"""Las tres dimensiones de la portada del docente y su bandera de disponibilidad (US-001, D7).

La historia que construye la pantalla de una dimensión cambia aquí su entrada: pone
``disponible=True`` y el ``url_name`` de esa pantalla (US-030 lo hará con Asistencia).
``test_dimensiones.py`` falla si una dimensión disponible no resuelve su ruta, para que ninguna
tarjeta enlace a una página que no existe (spec pantallas-de-inicio).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    """Una tarjeta de la portada. ``icono`` es el nombre del SVG en ``templates/iconos/``."""

    clave: str
    titulo: str
    subtitulo: str
    verbo: str
    icono: str
    url_name: str | None = None
    disponible: bool = False


# En el orden de las tarjetas (DESIGN.md, Tarjeta de dimensión G4e).
DIMENSIONES = (
    Dimension(
        "sesiones",
        "Sesiones",
        "Planificación de sesiones de aprendizaje",
        "Ver sesiones",
        "book-open",
    ),
    Dimension(
        "notas",
        "Notas",
        "Registro y control de notas",
        "Registrar notas",
        "clipboard-list",
    ),
    Dimension(
        "asistencia",
        "Asistencia",
        "Control de asistencia",
        "Registrar asistencia",
        "calendar-check",
    ),
)


def tarjeta_inicial(dimensiones):
    """Clave de la tarjeta inicial del carrusel: la primera disponible o, si no hay, la primera."""
    return next((d.clave for d in dimensiones if d.disponible), dimensiones[0].clave)
