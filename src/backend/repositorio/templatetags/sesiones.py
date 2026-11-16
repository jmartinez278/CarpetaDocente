"""Filtros de las plantillas de Sesiones (US-011)."""

from django import template
from django.utils import formats

register = template.Library()

KILOBYTE = 1024
MEGABYTE = 1024 * 1024
ESPACIO_FIJO = "\xa0"


@register.filter
def tamano(bytes_):
    """«142 KB» por debajo de 1 MB y «1,2 MB» desde ahí; el mismo formato que ``sesiones.js``."""
    if bytes_ < MEGABYTE:
        return f"{max(1, round(bytes_ / KILOBYTE))}{ESPACIO_FIJO}KB"
    return f"{formats.number_format(round(bytes_ / MEGABYTE, 1), 1)}{ESPACIO_FIJO}MB"
