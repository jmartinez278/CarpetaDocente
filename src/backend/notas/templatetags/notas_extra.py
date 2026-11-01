"""Filtro de la plantilla de competencias (design de US-029, D9)."""

from django import template

register = template.Library()


@register.filter
def cuenta_marcadas(area, marcadas):
    """Cuántas competencias del ``AreaDeLaSeccion`` están en el conjunto ``marcadas`` (de id)."""
    return sum(1 for competencia in area.competencias if competencia.pk in marcadas)
