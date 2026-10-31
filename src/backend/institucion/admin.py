"""Registro de institucion en el panel de administración (rol Administrador)."""

from copy import copy

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import connection
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from actividad.models import Operacion
from actividad.panel import AGREGAR, RegistraEnPanel
from institucion import servicios
from institucion.models import AnioEscolar, Institucion, Periodo, Seccion


class FormularioInstitucion(forms.ModelForm):
    """Ficha de la institución: la organización no cambia si ya hay periodos (US-028, D5)."""

    class Meta:
        model = Institucion
        fields = ["nombre", "codigo_modular", "organizacion_periodos"]

    def clean(self):
        """Repite la regla para la ficha que se abrió con el campo editable, antes de los periodos.

        En un POST la institución llega releída con ``FOR UPDATE`` (``RegistraEnPanel``): un
        ``guardar_periodos`` del mismo momento espera a que esta ficha termine.
        """
        datos = super().clean()
        if "organizacion_periodos" in datos:
            propuesta = copy(self.instance)
            propuesta.organizacion_periodos = datos["organizacion_periodos"]
            servicios.validar_organizacion(propuesta)
        return datos


@admin.register(Institucion)
class InstitucionAdmin(RegistraEnPanel, admin.ModelAdmin):
    """Pantalla del Administrador para las instituciones."""

    form = FormularioInstitucion
    list_display = ["nombre", "codigo_modular", "organizacion_periodos", "creado_en"]
    search_fields = ["nombre", "codigo_modular"]

    def get_readonly_fields(self, request, obj=None):
        """Con periodos guardados, la organización se muestra de solo lectura (D5)."""
        if obj is not None and Periodo.objects.filter(anio_escolar__institucion=obj).exists():
            return ["organizacion_periodos"]
        return []

    def has_delete_permission(self, request, obj=None):
        """Borrar una institución borraría en cascada todo lo suyo (RN-023; US-008, D4)."""
        return False

    def operacion_del_panel(self, request, obj, accion, campos):
        if accion == AGREGAR:
            return [(Operacion.INSTITUCION_CREADA, None)]
        return [(Operacion.INSTITUCION_EDITADA, {"campos": campos})]


# En ``request``: el ``ValidationError`` de ``guardar_periodos``, para la ficha que se vuelve
# a mostrar con él.
ERROR_AL_GUARDAR = "_error_al_guardar_periodos"


class FormularioPeriodo(forms.ModelForm):
    """Una fila de periodo: las fechas pueden ir vacías y las reglas las da el conjunto (D2)."""

    class Meta:
        model = Periodo
        fields = ["fecha_inicio", "fecha_fin"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.required = False

    def _get_validation_exclusions(self):
        """Sin las restricciones del modelo en la fila (D3): ``ex_periodo_cruce`` compararía las
        fechas nuevas con las viejas de las otras filas, y ``ck_periodo_fechas`` repetiría con
        otro texto lo que ``validar_periodos`` dice en la fila."""
        return super()._get_validation_exclusions() | {"anio_escolar", "fecha_inicio", "fecha_fin"}


class FormsetPeriodos(BaseInlineFormSet):
    """Las N filas de un año se validan juntas con ``validar_periodos`` (D2 y D5)."""

    def add_fields(self, form, index):
        """El número lo pone la posición: las filas nuevas lo muestran antes de guardarse."""
        super().add_fields(form, index)
        if index is not None and form.instance.numero is None:
            form.instance.numero = index + 1
        # La tabla da el nombre de la columna, no el de cada campo: sin esto, las fechas no
        # tienen etiqueta para el lector de pantalla (axe ``label``).
        numero = index + 1 if index is not None else "nuevo"
        form.fields["fecha_inicio"].widget.attrs["aria-label"] = (
            f"Periodo {numero}: fecha de inicio"
        )
        form.fields["fecha_fin"].widget.attrs["aria-label"] = f"Periodo {numero}: fecha de fin"

    def filas(self):
        return [
            (numero, form.cleaned_data.get("fecha_inicio"), form.cleaned_data.get("fecha_fin"))
            for numero, form in enumerate(self.forms, start=1)
        ]

    def clean(self):
        error = getattr(self.request, ERROR_AL_GUARDAR, None)
        if error is not None:
            self.poner_error(error)
        if not self.has_changed() or any(form.errors for form in self.forms):
            return
        try:
            servicios.validar_periodos(self.instance, self.filas())
        except ValidationError as error:
            self.poner_error(error)

    def poner_error(self, error):
        """Los errores de una fila llegan con su número como clave; los del conjunto, sin él."""
        if not hasattr(error, "error_dict"):
            raise error
        for numero, mensajes in error.error_dict.items():
            self.forms[numero - 1].add_error(None, mensajes)


class PeriodoInline(admin.TabularInline):
    """Los periodos dentro de la ficha de un año guardado, sin borrar (RN-023; D5)."""

    model = Periodo
    form = FormularioPeriodo
    formset = FormsetPeriodos
    fields = ["numero", "fecha_inicio", "fecha_fin"]
    readonly_fields = ["numero"]
    can_delete = False

    def cantidad(self, obj):
        """Filas de la ficha; con el año CERRADO, solo las guardadas (no hay filas para llenar)."""
        if not self.abierto(obj):
            return obj.periodos.count()
        return servicios.PERIODOS_POR_ORGANIZACION.get(obj.institucion.organizacion_periodos, 0)

    def get_extra(self, request, obj=None, **kwargs):
        return max(self.cantidad(obj) - obj.periodos.count(), 0)

    def get_max_num(self, request, obj=None, **kwargs):
        return self.cantidad(obj)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    def abierto(self, obj):
        return obj is not None and obj.estado == AnioEscolar.Estado.ABIERTO

    def has_add_permission(self, request, obj=None):
        return self.abierto(obj) and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """Año CERRADO: los periodos son de solo lectura."""
        return self.abierto(obj) and super().has_change_permission(request, obj)


@admin.register(AnioEscolar)
class AnioEscolarAdmin(RegistraEnPanel, admin.ModelAdmin):
    """Años escolares: institución, año y estado (US-005, D1); sin los campos de RF-009.

    En la ficha de un año guardado, sus periodos (US-028, D5).
    """

    readonly_fields = ["aviso_periodos"]
    list_display = ["anio", "institucion", "estado"]
    list_filter = ["estado", "institucion"]
    list_select_related = ["institucion"]

    def get_readonly_fields(self, request, obj=None):
        """Con periodos guardados el año no cambia de institución: saltaría la organización fija
        (D5) y dejaría periodos de otra organización."""
        campos = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.periodos.exists():
            campos.append("institucion")
        return campos

    def get_fields(self, request, obj=None):
        if obj is not None and not obj.institucion.organizacion_periodos:
            return ["institucion", "anio", "estado", "aviso_periodos"]
        return ["institucion", "anio", "estado"]

    @admin.display(description="periodos")
    def aviso_periodos(self, obj):
        enlace = reverse("admin:institucion_institucion_change", args=[obj.institucion_id])
        return format_html(
            '{} <a href="{}">Ir a la institución</a>', servicios.SIN_ORGANIZACION, enlace
        )

    def get_inlines(self, request, obj):
        """Solo en la ficha de un año guardado cuya institución tiene organización."""
        if obj is None or not obj.institucion.organizacion_periodos:
            return []
        return [PeriodoInline]

    def get_object(self, request, object_id, from_field=None):
        """En un POST bloquea la institución del año y después deja que ``RegistraEnPanel``
        bloquee el año: el orden de ``guardar_periodos`` (D4). Con el inverso, la ficha y un
        guardado de periodos del mismo momento se esperarían uno al otro (deadlock)."""
        if request.method == "POST" and connection.in_atomic_block:
            try:
                anios = AnioEscolar.objects.filter(pk=object_id).values("institucion_id")
                list(Institucion.objects.select_for_update().filter(pk__in=anios))
            except (ValidationError, ValueError):
                pass  # id inválido: ``super()`` devuelve ``None`` y la ficha da 404
        return super().get_object(request, object_id, from_field)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Un ``ValidationError`` de ``guardar_periodos`` (carrera que el formset no vio, D4) llega
        con la ficha ya revertida: se vuelve a mostrar con el POST y el mensaje, sin 500."""
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except ValidationError as error:
            setattr(request, ERROR_AL_GUARDAR, error)
            return super().changeform_view(request, object_id, form_url, extra_context)

    def save_formset(self, request, form, formset, change):
        """Los periodos se escriben con ``guardar_periodos``, nunca con ``formset.save()`` (D4)."""
        if formset.model is not Periodo:
            return super().save_formset(request, form, formset, change)
        # ``construct_change_message`` los lee; lo que cambió queda en el registro de actividad.
        formset.new_objects, formset.changed_objects, formset.deleted_objects = [], [], []
        if formset.has_changed():
            servicios.guardar_periodos(form.instance, formset.filas(), request.user)
        return None

    def has_delete_permission(self, request, obj=None):
        """Borrar un año borraría en cascada sus secciones (RN-023; el cierre es RF-009)."""
        return False

    def operacion_del_panel(self, request, obj, accion, campos):
        if accion == AGREGAR:
            return [(Operacion.ANIO_CREADO, None)]
        return [(Operacion.ANIO_EDITADO, {"campos": campos})]


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
class SeccionAdmin(RegistraEnPanel, admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        """Guarda en ``request`` el docente anterior para SECCION_ASIGNADA o LIBERADA (D5)."""
        if change:
            request._docente_anterior = form.initial.get("docente")
        super().save_model(request, obj, form, change)

    def operacion_del_panel(self, request, obj, accion, campos):
        """El docente da SECCION_ASIGNADA (elegido o cambiado) o SECCION_LIBERADA (quitado); el
        grado o el nombre, SECCION_EDITADA. Si cambian los dos, quedan dos entradas."""
        if accion == AGREGAR:
            return [(Operacion.SECCION_CREADA, None)]
        anterior = request.__dict__.pop("_docente_anterior", None)
        operaciones = []
        otros = [campo for campo in campos if campo != "docente"]
        if otros:
            operaciones.append((Operacion.SECCION_EDITADA, {"campos": otros}))
        if "docente" in campos:
            docentes = {
                "docente_anterior": anterior,
                "docente_nuevo": obj.docente_id,
            }
            asignada = obj.docente_id is not None
            operacion = Operacion.SECCION_ASIGNADA if asignada else Operacion.SECCION_LIBERADA
            operaciones.append((operacion, docentes))
        return operaciones
