"""Registro de actividad en el panel: consulta de solo lectura del Administrador (D8 y D11)."""

from datetime import date, timedelta

from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from actividad import servicios
from actividad.forms import FormularioRango
from actividad.models import RegistroActividad
from cuentas.models import Usuario


class RangoFechasFilter(admin.FieldListFilter):
    """Filtro "desde – hasta" por días de Lima, ambos incluidos (D11).

    El ``DateFieldListFilter`` de Django solo ofrece "hoy, últimos 7 días, este mes, este año".
    Cualquiera de las dos fechas puede quedar vacía.
    """

    template = "admin/actividad/filtro_rango.html"

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.parametro_desde = f"{field_path}__desde"
        self.parametro_hasta = f"{field_path}__hasta"
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = "rango de fechas"

    def expected_parameters(self):
        return [self.parametro_desde, self.parametro_hasta]

    def _valor(self, parametro):
        valor = self.used_parameters.get(parametro)
        if isinstance(valor, list):
            valor = valor[-1] if valor else ""
        return valor or ""

    def _fecha(self, parametro):
        valor = self._valor(parametro)
        if not valor:
            return None
        try:
            return date.fromisoformat(valor)
        except ValueError as error:
            raise IncorrectLookupParameters(error) from error

    def queryset(self, request, queryset):
        desde, hasta = self._fecha(self.parametro_desde), self._fecha(self.parametro_hasta)
        if desde:
            queryset = queryset.filter(
                **{f"{self.field_path}__gte": servicios.inicio_del_dia(desde)}
            )
        if hasta:
            queryset = queryset.filter(
                **{f"{self.field_path}__lt": servicios.inicio_del_dia(hasta + timedelta(days=1))}
            )
        return queryset

    def choices(self, changelist):
        """Una sola "opción": los valores del formulario y los demás filtros como ocultos."""
        propios = set(self.expected_parameters())
        yield {
            "desde": self._valor(self.parametro_desde),
            "hasta": self._valor(self.parametro_hasta),
            "parametro_desde": self.parametro_desde,
            "parametro_hasta": self.parametro_hasta,
            "ocultos": [(k, v) for k, v in changelist.params.items() if k not in propios],
            "limpiar": changelist.get_query_string(remove=list(propios)),
            "puesto": any(self.used_parameters.values()),
        }


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    """Consulta del registro: nadie agrega, cambia ni borra, ni el Administrador (D8)."""

    list_display = ["fecha_hora_lima", "usuario", "operacion", "entidad", "entidad_id"]
    list_filter = [
        "operacion",
        ("usuario", admin.RelatedOnlyFieldListFilter),
        ("fecha_hora", RangoFechasFilter),
    ]
    list_select_related = ["usuario"]
    list_per_page = 50
    actions = None

    @admin.display(description="fecha y hora (Lima)", ordering="fecha_hora")
    def fecha_hora_lima(self, entrada):
        return timezone.localtime(entrada.fecha_hora, servicios.LIMA).strftime(
            servicios.FORMATO_FECHA_HORA
        )

    def get_urls(self):
        propias = [
            path(
                "exportar/",
                self.admin_site.admin_view(self.exportar_view),
                name="actividad_registroactividad_exportar",
            ),
            path(
                "indicadores/",
                self.admin_site.admin_view(self.indicadores_view),
                name="actividad_registroactividad_indicadores",
            ),
        ]
        return propias + super().get_urls()

    def exportar_view(self, request):
        """Descarga el registro con los filtros de la lista (D10). Solo por POST."""
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.has_view_permission(request):
            raise PermissionDenied
        try:
            lista = self.get_changelist_instance(request)
        except IncorrectLookupParameters:
            return HttpResponseRedirect(reverse("admin:actividad_registroactividad_changelist"))
        texto = servicios.exportar_csv(lista.queryset, request.user, request.GET.items())
        respuesta = HttpResponse(texto, content_type="text/csv; charset=utf-8")
        nombre = (
            f"registro-actividad-{timezone.localtime(timezone.now(), servicios.LIMA):%Y%m%d-%H%M}"
        )
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}.csv"'
        return respuesta

    def indicadores_view(self, request):
        """ "Indicadores por semana" (D9). Sin fechas, el rango por defecto."""
        if not self.has_view_permission(request):
            raise PermissionDenied
        if "desde" in request.GET or "hasta" in request.GET:
            formulario = FormularioRango(request.GET)
        else:
            desde, hasta = servicios.rango_por_defecto(timezone.localdate())
            formulario = FormularioRango({"desde": desde, "hasta": hasta})
        filas = []
        if formulario.is_valid():
            datos = formulario.cleaned_data
            filas = servicios.indicadores_por_semana(datos["desde"], datos["hasta"])
        contexto = {
            **self.admin_site.each_context(request),
            "title": "Indicadores por semana",
            "opts": self.opts,
            "formulario": formulario,
            "filas": filas,
        }
        return TemplateResponse(request, "admin/actividad/indicadores.html", contexto)

    def has_view_permission(self, request, obj=None):
        usuario = request.user
        return usuario.is_active and getattr(usuario, "rol", None) == Usuario.Rol.ADMINISTRADOR

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
