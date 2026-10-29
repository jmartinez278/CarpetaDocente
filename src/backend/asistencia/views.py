"""Vistas de la asistencia de hoy (design de US-030, D3 y D10).

Solo leen la petición y llaman a ``asistencia.servicios``. El acceso es el de la lista de
estudiantes (``SeccionDocenteMixin``): otra docente o un año CERRADO, 404; otro rol y sin sesión,
``RolRequeridoMixin``, con ``HX-Redirect`` cuando el guardado llega con ``HX-Request``.
Los guardados responden sin cuerpo: 204 guardado, 400 estado o nota que no valen, 404 estudiante
que no es activo de la sección y 409 fecha que no es hoy o no es día de clases (D3).
"""

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from asistencia import servicios
from institucion.models import Estudiante
from institucion.views import SeccionDocenteMixin


def sin_cuerpo(status):
    return HttpResponse(status=status)


class HoyView(SeccionDocenteMixin, View):
    """La pantalla de la asistencia de hoy; abrirla no crea la jornada."""

    def get(self, request, seccion_id):
        hoy = timezone.localdate()
        contexto = {
            "seccion": self.seccion,
            "fecha": hoy,
            "texto_fecha": servicios.texto_fecha(hoy),
            "lista": servicios.lista_de_hoy(self.seccion, hoy),
        }
        return render(request, "asistencia/hoy.html", contexto)


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
