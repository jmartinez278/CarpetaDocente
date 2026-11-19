"""Vistas de la asistencia de un día (design de US-030, D3 y D10; US-031, D2).

Solo leen la petición y llaman a ``asistencia.servicios``. El acceso es el de la lista de
estudiantes (``SeccionDocenteMixin``): sección ajena, inexistente o de un año CERRADO, o un
estudiante de la ruta que no es de ella, 403 con registro (US-004); otro rol y sin sesión,
``RolRequeridoMixin``, con ``HX-Redirect`` cuando el guardado llega con ``HX-Request``.
Los guardados responden sin cuerpo: 204 guardado, 400 estado o nota que no valen, 404 estudiante
de la sección que no está activo y 409 fecha que no se puede abrir (D3). Abrir una fecha que no
se puede abrir da 404 (US-031, D2).
"""

from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from asistencia import servicios
from institucion.models import Estudiante
from institucion.servicios import texto_seccion_corto
from institucion.views import SeccionDocenteMixin


def sin_cuerpo(status):
    return HttpResponse(status=status)


class AsistenciaDelDiaView(SeccionDocenteMixin, View):
    """La pantalla de la asistencia de un día; abrirla no crea la jornada.

    ``HoyView`` y ``DiaView`` comparten el contexto y solo cambian la fecha que abren.
    """

    def fecha_abierta(self, hoy):
        raise NotImplementedError

    def get(self, request, seccion_id, **kwargs):
        hoy = timezone.localdate()
        fecha = self.fecha_abierta(hoy)
        seccion = self.seccion
        dia_de_clases = servicios.es_dia_de_clases(fecha)
        lista = servicios.lista_del_dia(seccion, fecha)

        def url_de(dia):
            if dia == hoy:
                return reverse("asistencia:hoy", args=[seccion.pk])
            return reverse("asistencia:dia", args=[seccion.pk, dia])

        inicio = servicios.inicio_del_anio(seccion.anio_escolar)
        contexto = {
            "seccion": seccion,
            "seccion_corta": texto_seccion_corto(seccion),
            "fecha": fecha,
            "hoy": hoy,
            "texto_fecha": servicios.texto_fecha(fecha),
            "semana": servicios.semana(fecha, hoy, inicio, url_de),
            "dia_de_clases": dia_de_clases,
            "lista": lista,
            "con_lista": dia_de_clases and bool(lista.filas),
            # El JS cambia el 0 por el id del estudiante de cada fila.
            "url_marcar": reverse("asistencia:marcar", args=[seccion.pk, fecha, 0]),
            "url_restantes": reverse("asistencia:restantes", args=[seccion.pk, fecha]),
        }
        return render(request, "asistencia/hoy.html", contexto)


class HoyView(AsistenciaDelDiaView):
    """``asistencia/``: hoy, o el aviso de fin de semana."""

    def fecha_abierta(self, hoy):
        return hoy


class DiaView(AsistenciaDelDiaView):
    """``asistencia/<fecha>/``: lo mismo que hoy para un día que ``se_puede_abrir``, si no, 404."""

    def fecha_abierta(self, hoy):
        fecha = self.kwargs["fecha"]
        if not servicios.se_puede_abrir(self.seccion, fecha, hoy):
            raise Http404
        return fecha


class GuardadoMixin(SeccionDocenteMixin):
    """Traduce los errores del servicio a las respuestas sin cuerpo de D3."""

    def guardar(self, guardado):
        try:
            guardado()
        except servicios.FechaNoValida:
            return sin_cuerpo(409)
        except ValidationError:
            return sin_cuerpo(400)
        except Estudiante.DoesNotExist:
            return sin_cuerpo(404)
        return sin_cuerpo(204)


class MarcarView(GuardadoMixin, View):
    """El estado de destino de un estudiante (POST ``estado`` y ``nota``), idempotente."""

    def post(self, request, seccion_id, fecha, estudiante_id):
        return self.guardar(
            lambda: servicios.marcar(
                self.seccion,
                estudiante_id,
                fecha,
                request.POST.get("estado", ""),
                request.POST.get("nota", ""),
                request.user,
            )
        )


class RestantesView(GuardadoMixin, View):
    """Asistió para los Sin marcar del lote (POST ``estudiante`` repetido), al acabar la cuenta."""

    def post(self, request, seccion_id, fecha):
        try:
            ids = [int(valor) for valor in request.POST.getlist("estudiante")]
        except ValueError:
            return sin_cuerpo(400)
        return self.guardar(
            lambda: servicios.marcar_restantes(self.seccion, ids, fecha, request.user)
        )
