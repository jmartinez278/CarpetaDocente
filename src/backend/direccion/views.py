"""Vistas del módulo direccion (US-040)."""

from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from asistencia.servicios import saludo
from cuentas.acceso import RolRequeridoMixin
from cuentas.models import Usuario
from direccion import servicios
from repositorio import servicios as repositorio
from repositorio.views import EntregaBase, no_disponible


class DireccionMixin(RolRequeridoMixin):
    """Reserva la vista al rol Dirección (D2): otro rol va a su inicio y una visita, al ingreso."""

    rol_requerido = Usuario.Rol.DIRECCION


class ConsolidadosView(DireccionMixin, TemplateView):
    """Consolidados de la dirección (US-040, D2, D3 y D4): el mapa de las secciones y el resumen
    de la I.E. en el periodo de ``?periodo=`` (si no vale, el vigente). Solo lee."""

    http_method_names = ["get", "head", "options"]
    template_name = "direccion/consolidados.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        institucion = self.request.user.institucion
        contexto["institucion"] = institucion
        contexto["url_base"] = reverse("direccion:consolidados")
        contexto["datos"] = servicios.consolidados(
            institucion, self.request.GET.get("periodo", ""), timezone.localdate()
        )
        return contexto


class SeccionView(DireccionMixin, View):
    """Una pestaña del detalle de una sección (D2). Solo lectura: ``seccion_de_la_direccion``
    da 404 para otra institución, un año CERRADO o una sección que no existe.

    Las tres pestañas comparten la cabecera, la tira de bimestres y el recuadro café; cada una
    pone su contenido en ``contexto_de_la_pestana``. Notas y Asistencia de una sección sin
    estudiantes llevan (302) a Sesiones, con el mismo ``?periodo=``.
    """

    http_method_names = ["get", "head", "options"]
    pestana = ""

    @property
    def template_name(self):
        return f"direccion/seccion_{self.pestana}.html"

    def get(self, request, id_seccion):
        seccion = servicios.seccion_de_la_direccion(request.user, id_seccion)
        pedido = request.GET.get("periodo", "")
        detalle = servicios.detalle_de_la_seccion(seccion, pedido, timezone.localdate())
        if self.pestana != "sesiones" and not detalle.estudiantes:
            consulta = f"?{urlencode({'periodo': pedido})}" if pedido else ""
            return redirect(reverse("direccion:sesiones", args=[seccion.pk]) + consulta)
        contexto = {
            "seccion": seccion,
            "detalle": detalle,
            "datos": detalle.datos,
            "pestanas": detalle.pestanas(),
            "pestana": self.pestana,
            "url_base": reverse(f"direccion:{self.pestana}", args=[seccion.pk]),
        }
        if detalle.datos.elegido is not None:
            contexto.update(self.contexto_de_la_pestana(request, detalle))
        return render(request, self.template_name, contexto)

    def contexto_de_la_pestana(self, request, detalle):
        return {}


class NotasView(SeccionView):
    """Pestaña Notas: la tabla por área y la hoja del área elegida (``?area=``), con el filtro
    ``?filtro=pendientes``. Una consulta que no vale se ignora (D2)."""

    pestana = "notas"

    def contexto_de_la_pestana(self, request, detalle):
        periodo = detalle.datos.elegido.periodo
        return {
            "notas": servicios.notas_del_detalle(
                detalle.seccion, periodo, request.GET.get("area", ""), request.GET.get("filtro", "")
            )
        }


class AsistenciaView(SeccionView):
    """Pestaña Asistencia: los días de clase y los totales por estudiante y por sección."""

    pestana = "asistencia"

    def contexto_de_la_pestana(self, request, detalle):
        periodo = detalle.datos.elegido.periodo
        return {
            "asistencia": servicios.asistencia_del_detalle(
                detalle.seccion, periodo, detalle.datos.hoy
            )
        }


class SesionesView(SeccionView):
    """Pestaña Sesiones: la semana y las tarjetas de la tutora (``?dia=``) y, aparte, los
    docentes de curso del grado."""

    pestana = "sesiones"

    def contexto_de_la_pestana(self, request, detalle):
        elegido = detalle.datos.elegido
        base = reverse("direccion:sesiones", args=[detalle.seccion.pk])

        def url_de(fecha):
            return f"{base}?{urlencode({'periodo': elegido.numero, 'dia': fecha.isoformat()})}"

        return {
            "sesiones": servicios.sesiones_del_detalle(
                detalle.seccion,
                elegido.periodo,
                detalle.datos.hoy,
                request.GET.get("dia", ""),
                url_de,
            )
        }


def _volver_a_consolidados():
    return ("Consolidados", "Volver a Consolidados", reverse("direccion:consolidados"))


class SesionView(DireccionMixin, View):
    """La página de una sesión para la dirección (D2 y D7): la de la docente sin migas, acciones
    de la autora ni total de vistas, y sin contar una vista (la dirección no es colega)."""

    http_method_names = ["get", "head", "options"]

    def get(self, request, id_sesion):
        sesion = repositorio.sesion_visible_direccion(request.user, id_sesion)
        if sesion is None:
            return no_disponible(request, _volver_a_consolidados())
        contexto = {
            "sesion": sesion,
            "grado": sesion.grados_texto,
            "referencia": False,
            "url_descargar": reverse("direccion:descargar", args=[sesion.pk]),
            "url_ver": reverse("direccion:ver", args=[sesion.pk]),
        }
        return render(request, "direccion/sesion.html", contexto)


class EntregarView(DireccionMixin, EntregaBase):
    """«Descargar» y «Ver» para la dirección: la misma entrega, con su puerta de visibilidad."""

    http_method_names = ["get", "head", "options"]
    visible = staticmethod(repositorio.sesion_visible_direccion)

    def no_disponible(self, request):
        return no_disponible(request, _volver_a_consolidados())


class InicioDireccionView(RolRequeridoMixin, TemplateView):
    """Portada de la dirección (spec pantallas-de-inicio, «Inicio de la dirección»; D9).

    Saluda según la hora de Lima como la del docente y lleva la banda de Consolidados con las
    secciones atrasadas del bimestre vigente, Entregas (próximamente) y el cierre del bimestre,
    con el botón que abre la plantilla del SIAGIE.
    """

    rol_requerido = Usuario.Rol.DIRECCION
    template_name = "direccion/inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        institucion = self.request.user.institucion
        contexto["saludo"] = saludo(timezone.localtime().hour)
        contexto["institucion"] = institucion
        contexto["inicio"] = servicios.inicio_de_la_direccion(institucion, timezone.localdate())
        return contexto
