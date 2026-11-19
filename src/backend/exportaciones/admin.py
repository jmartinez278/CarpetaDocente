"""Panel de exportaciones: las equivalencias de sección, solo para verlas (design D5).

El único camino que las crea o las borra es el llenado de la plantilla, con su registro de
actividad; por eso el panel no agrega, no cambia ni borra.
"""

from django.contrib import admin

from exportaciones.models import EquivalenciaSeccion


@admin.register(EquivalenciaSeccion)
class EquivalenciaSeccionAdmin(admin.ModelAdmin):
    list_display = ["seccion", "grado", "codigo_siagie", "nombre_siagie", "creado_en"]
    list_filter = ["anio_escolar"]
    list_select_related = ["seccion__anio_escolar"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
