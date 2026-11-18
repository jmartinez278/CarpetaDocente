"""Panel del Administrador para las sesiones de referencia (design de US-018, D4 y D5).

Solo se ven las sesiones de referencia (el proxy ``SesionReferencia``): las de las docentes no
están en el panel (RN-015). La ficha arma el formulario y llama a ``servicios``, que valida,
guarda el archivo y deja la entrada de actividad; aquí no se escribe en la base.
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import Http404
from django.template.defaultfilters import filesizeformat

from actividad.models import Operacion
from actividad.panel import RegistraEnPanel
from institucion.models import Institucion
from repositorio import servicios
from repositorio.models import SesionReferencia

# Lo que la ficha manda al servicio, como texto; el archivo va aparte.
CAMPOS = (
    "institucion",
    "grado",
    "grado_hasta",
    "area",
    "titulo",
    "proposito",
    "fuente",
    "permiso_uso",
)
_GRADOS = [("", "---------"), *servicios.GRADOS]


class FormularioReferencia(forms.ModelForm):
    """Todos los campos opcionales: las reglas y sus mensajes los da ``validar_referencia``."""

    grado = forms.TypedChoiceField(
        label="grado inicial", choices=_GRADOS, coerce=int, empty_value=None, required=False
    )
    grado_hasta = forms.TypedChoiceField(
        label="grado final", choices=_GRADOS, coerce=int, empty_value=None, required=False
    )
    archivo = forms.FileField(
        label="archivo",
        required=False,
        help_text="PDF o Word (.docx) de hasta 4 MB. No se cambia después: para otro archivo, "
        "elimine la sesión y cárguela de nuevo.",
    )

    class Meta:
        model = SesionReferencia
        fields = list(CAMPOS)
        help_texts = {
            "fuente": "De dónde viene la sesión; si la hizo el equipo, «Equipo del proyecto».",
            "permiso_uso": "Con qué permiso se usa (RN-020).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.required = False

    def _get_validation_exclusions(self):
        """Sin la validación del modelo: la da el servicio, y los ``CHECK`` son la red."""
        return {campo.name for campo in self.instance._meta.fields}

    def datos(self):
        """Lo que se manda al servicio. La institución de una ficha guardada es la suya."""
        datos = {campo: str(self.data.get(campo) or "") for campo in CAMPOS}
        if self.instance.pk is not None:
            datos["institucion"] = str(self.instance.institucion_id)
        return datos

    def clean(self):
        limpios = super().clean()
        al_crear = self.instance.pk is None
        try:
            servicios.validar_referencia(self.datos(), limpios.get("archivo"), al_crear)
        except ValidationError as error:
            for campo, mensajes in error.message_dict.items():
                destino = campo if campo in self.fields else None
                self.add_error(destino, mensajes)
        return limpios


@admin.register(SesionReferencia)
class SesionReferenciaAdmin(RegistraEnPanel, admin.ModelAdmin):
    """Cargar, editar y eliminar material de referencia. El servicio deja la entrada; la mezcla
    se usa por su ``FOR UPDATE`` y su regla de borrado (D4, D5)."""

    form = FormularioReferencia
    operacion_al_borrar = Operacion.SESION_REFERENCIA_ELIMINADA
    list_display = ["titulo", "grados", "area", "institucion", "fuente", "creado_en"]
    list_select_related = ["area", "institucion"]
    search_fields = ["titulo"]
    ordering = ["-creado_en"]

    @admin.display(description="grados", ordering="grado")
    def grados(self, obj):
        return obj.grados_texto

    @admin.display(description="tipo")
    def tipo(self, obj):
        return obj.tipo_corto

    @admin.display(description="tamaño")
    def tamano(self, obj):
        return filesizeformat(obj.tamano_bytes)

    def get_fields(self, request, obj=None):
        if obj is None:
            return [*CAMPOS, "archivo"]
        return ["institucion", *CAMPOS[1:], "archivo_nombre", "tipo", "tamano"]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        return ["institucion", "archivo_nombre", "tipo", "tamano"]

    def get_changeform_initial_data(self, request):
        """Con una sola institución, viene elegida."""
        inicial = super().get_changeform_initial_data(request)
        instituciones = list(Institucion.objects.values_list("pk", flat=True)[:2])
        if len(instituciones) == 1:
            inicial.setdefault("institucion", instituciones[0])
        return inicial

    def get_object(self, request, object_id, from_field=None):
        """Lo que no es una sesión de referencia no existe en el panel: 404, no un aviso."""
        obj = super().get_object(request, object_id, from_field)
        if obj is None:
            raise Http404
        return obj

    def save_model(self, request, obj, form, change):
        if change:
            guardada = servicios.editar_referencia(request.user, obj, form.datos())
        else:
            guardada = servicios.cargar_referencia(
                request.user, form.datos(), form.cleaned_data.get("archivo")
            )
        # La respuesta y el historial del panel leen ``obj``: queda como la fila guardada.
        for campo in guardada._meta.concrete_fields:
            setattr(obj, campo.attname, getattr(guardada, campo.attname))
        obj._state.adding = False
        obj._state.db = guardada._state.db

    def operacion_del_panel(self, request, obj, accion, campos):
        return []  # el servicio ya registró

    def delete_model(self, request, obj):
        servicios.eliminar_referencia(request.user, obj)

    def get_actions(self, request):
        """Sin «eliminar seleccionadas»: se borra de a una, desde la ficha (D5)."""
        acciones = super().get_actions(request)
        acciones.pop("delete_selected", None)
        return acciones

    def delete_queryset(self, request, queryset):
        raise NotImplementedError("Las sesiones de referencia se eliminan de a una (US-018, D5).")
