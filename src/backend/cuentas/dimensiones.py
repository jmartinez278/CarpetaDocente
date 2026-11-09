"""Las tres dimensiones de la portada del docente y su bandera de disponibilidad (US-001, D7).

La historia que construye la pantalla de una dimensión cambia aquí su entrada: pone
``disponible=True`` y el ``url_name`` de esa pantalla. ``test_dimensiones.py`` falla si una
dimensión disponible no resuelve su ruta, para que ninguna tarjeta enlace a una página que no existe
(spec pantallas-de-inicio). Desde US-030, Asistencia está disponible, y desde US-020, Notas; sus
rutas son de la sección, así que la portada las enlaza solo si la docente tiene una sola sección
(``para_portada``).
"""

from dataclasses import dataclass, replace

from django.urls import reverse

# Dimensiones cuya pantalla es de una sección: su ruta lleva el id de la sección.
POR_SECCION = {"notas", "asistencia"}


@dataclass(frozen=True)
class Dimension:
    """Una tarjeta de la portada. ``icono`` es el nombre del SVG en ``templates/iconos/``.

    ``url`` la arma ``para_portada`` a partir de ``url_name``; la tarjeta solo lee ``url``.
    """

    clave: str
    titulo: str
    subtitulo: str
    verbo: str
    icono: str
    url_name: str | None = None
    disponible: bool = False
    url: str | None = None


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
        url_name="notas:hoja",
        disponible=True,
    ),
    Dimension(
        "asistencia",
        "Asistencia",
        "Control de asistencia",
        "Registrar asistencia",
        "calendar-check",
        url_name="asistencia:hoy",
        disponible=True,
    ),
)


def para_portada(dimensiones, seccion):
    """Las tarjetas con su ``url``. Sin ``seccion`` (ninguna o varias), las de sección quedan en
    "Próximamente", con la misma regla que "Ver estudiantes" (design de US-030, D10)."""
    tarjetas = []
    for dimension in dimensiones:
        if dimension.disponible and dimension.clave in POR_SECCION:
            if seccion is None:
                dimension = replace(dimension, disponible=False)
            else:
                dimension = replace(dimension, url=reverse(dimension.url_name, args=[seccion.pk]))
        elif dimension.disponible:
            dimension = replace(dimension, url=reverse(dimension.url_name))
        tarjetas.append(dimension)
    return tuple(tarjetas)


def tarjeta_inicial(dimensiones):
    """Clave de la tarjeta inicial del carrusel: la primera disponible o, si no hay, la primera."""
    return next((d.clave for d in dimensiones if d.disponible), dimensiones[0].clave)


@dataclass(frozen=True)
class Destino:
    """Un destino del ☰. ``url`` en ``None`` se ve como "Próximamente", sin enlace."""

    clave: str
    titulo: str
    icono: str
    url: str | None
    actual: bool = False


# Orden del ☰ (spec pantallas-de-inicio, «Navegación de la docente»).
ORDEN_NAVEGACION = ("sesiones", "asistencia", "notas")

# Espacio de nombres de la vista → destino que marca como actual (rebrand-base, D6).
DESTINO_POR_ESPACIO = {
    "sesiones": "sesiones",
    "asistencia": "asistencia",
    "notas": "notas",
    "competencias": "notas",
}


def _destino_actual(vista_actual):
    """Clave del destino de la vista ``"espacio:nombre"``; ``None`` si no corresponde a ninguno."""
    if vista_actual == "docente:portada":
        return "inicio"
    espacio = (vista_actual or "").partition(":")[0]
    return DESTINO_POR_ESPACIO.get(espacio)


def navegacion_docente(seccion, vista_actual, dimensiones=DIMENSIONES):
    """Destinos del ☰: Inicio y las tres dimensiones con la regla de las tarjetas (D6).

    ``vista_actual`` es el ``view_name`` de la vista (``request.resolver_match``). Solo un
    destino con enlace puede ser el actual.
    """
    tarjetas = {d.clave: d for d in para_portada(dimensiones, seccion)}
    actual = _destino_actual(vista_actual)
    destinos = [Destino("inicio", "Inicio", "house", reverse("docente:portada"))]
    destinos += [
        Destino(t.clave, t.titulo, t.icono, t.url if t.disponible else None)
        for t in (tarjetas[clave] for clave in ORDEN_NAVEGACION)
    ]
    return tuple(replace(d, actual=d.url is not None and d.clave == actual) for d in destinos)
