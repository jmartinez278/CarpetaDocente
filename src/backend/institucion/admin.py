"""Registro de Institución en el panel de administración (rol Administrador)."""

from django.contrib import admin

from institucion.models import Institucion


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    """Pantalla del Administrador para las instituciones."""

    list_display = ["nombre", "codigo_modular", "organizacion_periodos", "creado_en"]
    search_fields = ["nombre", "codigo_modular"]
