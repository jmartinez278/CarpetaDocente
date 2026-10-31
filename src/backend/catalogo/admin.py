"""Catálogo curricular en el panel de administración (rol Administrador; design de EN-06, D5).

El catálogo lo carga la migración ``0002``: desde el panel no se agrega ni se borra nada
(RN-023). Una competencia que ya no se usa se desactiva.
"""

from django.contrib import admin

from actividad.models import Operacion
from actividad.panel import RegistraEnPanel
from catalogo.models import Area, Competencia, InstitucionArea


class CatalogoFijoAdmin(RegistraEnPanel, admin.ModelAdmin):
    """Sin botón ni URL de agregar, y sin borrar uno por uno ni en lote.

    Cada cambio, desde la ficha o desde ``list_editable``, deja CATALOGO_EDITADO (US-008, D5).
    """

    def operacion_del_panel(self, request, obj, accion, campos):
        return [(Operacion.CATALOGO_EDITADO, {"campos": campos})]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Area)
class AreaAdmin(CatalogoFijoAdmin):
    """Áreas del SIAGIE: solo se cambia el orden."""

    fields = ["codigo_siagie", "nombre", "es_transversal", "admite_exoneracion", "orden"]
    readonly_fields = ["codigo_siagie", "nombre", "es_transversal", "admite_exoneracion"]
    list_display = ["codigo_siagie", "nombre", "orden", "es_transversal", "admite_exoneracion"]


@admin.register(Competencia)
class CompetenciaAdmin(CatalogoFijoAdmin):
    """Competencias de cada área: se cambian el orden y la marca «activa»."""

    fields = ["area", "nombre", "orden", "activa"]
    readonly_fields = ["area", "nombre"]
    list_display = ["area", "orden", "nombre", "activa"]
    list_filter = ["area", "activa"]
    list_select_related = ["area"]


@admin.register(InstitucionArea)
class InstitucionAreaAdmin(CatalogoFijoAdmin):
    """Áreas que trabaja cada institución (RN-007): «se trabaja» se cambia desde la lista."""

    fields = ["institucion", "area", "se_trabaja"]
    readonly_fields = ["institucion", "area"]
    list_display = ["institucion", "area", "se_trabaja"]
    list_display_links = ["area"]
    list_editable = ["se_trabaja"]
    list_filter = ["institucion"]
    list_select_related = ["institucion", "area"]
