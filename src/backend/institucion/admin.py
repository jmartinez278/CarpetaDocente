"""Registro de institucion en el panel de administración (rol Administrador)."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from institucion import servicios
from institucion.models import AnioEscolar, Institucion, Seccion


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    """Pantalla del Administrador para las instituciones."""

    list_display = ["nombre", "codigo_modular", "organizacion_periodos", "creado_en"]
    search_fields = ["nombre", "codigo_modular"]


@admin.register(AnioEscolar)
class AnioEscolarAdmin(admin.ModelAdmin):
    """Años escolares: institución, año y estado (US-005, D1); sin los campos de RF-009."""

    fields = ["institucion", "anio", "estado"]
    list_display = ["anio", "institucion", "estado"]
    list_filter = ["estado", "institucion"]
    list_select_related = ["institucion"]

    def has_delete_permission(self, request, obj=None):
        """Borrar un año borraría en cascada sus secciones (RN-023; el cierre es RF-009)."""
        return False


class FormularioFichaSeccion(forms.ModelForm):
    """Ficha de una sección guardada, donde se elige el docente de aula (US-005, D1 y D4)."""

    class Meta:
        model = Seccion
        fields = ["grado", "nombre", "docente"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["docente"].queryset = servicios.docentes_elegibles(self.instance)

    def clean(self):
        """Revisa que el grado y el nombre no repitan otra sección del año.

        El año es de solo lectura en la ficha, y un ``ModelForm`` no valida una restricción
        con un campo que no está en el formulario: sin esto, ``uq_seccion`` daría un 500.
        """
        datos = super().clean()
        grado, nombre = datos.get("grado"), datos.get("nombre")
        repetida = (
            Seccion.objects.filter(
                anio_escolar_id=self.instance.anio_escolar_id, grado=grado, nombre=nombre
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if repetida:
            raise ValidationError("El año escolar ya tiene una sección con ese grado y nombre.")
        return datos


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    """Secciones del año: el alta no tiene docente; se elige en la ficha (US-005, D4)."""

    list_display = ["__str__", "anio_escolar", "docente"]
    list_filter = ["anio_escolar", "grado"]
    list_select_related = ["anio_escolar__institucion", "docente"]
    search_fields = ["nombre", "docente__first_name", "docente__last_name"]

    def get_fields(self, request, obj=None):
        if obj is None:
            return ["anio_escolar", "grado", "nombre"]
        return ["anio_escolar", "grado", "nombre", "docente"]

    def get_readonly_fields(self, request, obj=None):
        """En la ficha el año no cambia, para que la lista de docentes no quede desfasada."""
        return ["anio_escolar"] if obj is not None else []

    def get_object(self, request, object_id, from_field=None):
        """En un POST carga la sección con ``FOR UPDATE``, dentro de la transacción de la ficha.

        Así, de dos Administradores que guardan a la vez, el segundo espera al primero y ve el
        mensaje de D3 en el formulario, no un 500 del ``save()``. ``of=("self",)`` bloquea solo
        la fila de la sección: el ``select_related`` del docente es un ``LEFT JOIN``.
        """
        if request.method != "POST":
            return super().get_object(request, object_id, from_field)
        queryset = self.get_queryset(request).select_for_update(of=("self",))
        field = Seccion._meta.pk if from_field is None else Seccion._meta.get_field(from_field)
        try:
            return queryset.get(**{field.name: field.to_python(object_id)})
        except (Seccion.DoesNotExist, ValidationError, ValueError):
            return None

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None:
            kwargs["form"] = FormularioFichaSeccion
        return super().get_form(request, obj, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """Borrar una sección borraría en cascada sus registros (RN-023)."""
        return False
