"""Etiquetas del marco del rebrand: el ☰ y la cuenta (rebrand-base, D6 y D7).

Solo pintan: los destinos y la línea de secciones salen de ``cuentas.dimensiones`` y de
``institucion.servicios``.
"""

from django import template

from cuentas.dimensiones import navegacion_docente
from institucion.servicios import seccion_unica, secciones_de_la_cuenta

register = template.Library()


@register.inclusion_tag("rb/menu_navegacion.html", takes_context=True)
def menu_docente(context):
    request = context["request"]
    vista = request.resolver_match.view_name if request.resolver_match else None
    return {"destinos": navegacion_docente(seccion_unica(request.user), vista)}


@register.inclusion_tag("rb/menu_cuenta.html", takes_context=True)
def menu_cuenta(context):
    usuario = context["request"].user
    return {"user": usuario, "secciones": secciones_de_la_cuenta(usuario)}


@register.filter
def partes_aviso(mensaje):
    """Parte el aviso de inactividad («título», línea en blanco, «detalle») en sus dos líneas."""
    titulo, _, detalle = str(mensaje).partition("\n\n")
    return titulo.strip(), detalle.strip()
