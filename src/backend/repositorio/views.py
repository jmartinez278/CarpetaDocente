"""Vistas de Sesiones (design de US-010, US-014 y EN-03, D7).

Solo leen la petición y llaman a ``repositorio.servicios``. Son del rol Docente, con o sin sección
(``RolRequeridoMixin``): la dirección y el Administrador van a su inicio sin registro de intento
(no es una ruta de sección, decisión 11) y una visita sin sesión, al ingreso; con ``HX-Request``,
por ``HX-Redirect``. El envío responde 201 con el fragmento del éxito o 400 con
``{"errores": {campo: mensaje}}``.
"""

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from cuentas.acceso import RolRequeridoMixin
from cuentas.models import Usuario
from repositorio import servicios


class DocenteMixin(RolRequeridoMixin):
    rol_requerido = Usuario.Rol.DOCENTE


class SesionesView(DocenteMixin, View):
    """La pantalla Sesiones: cabecera, estado vacío y el popup con los datos del formulario."""

    def get(self, request):
        contexto = servicios.datos_del_formulario(request.user)
        return render(request, "repositorio/sesiones.html", contexto)


class EnviarSesionView(DocenteMixin, View):
    """El envío del popup (POST con los datos, el archivo y, si comparte, la aceptación)."""

    http_method_names = ["post"]

    def post(self, request):
        try:
            sesion = servicios.enviar_sesion(
                request.user, request.POST, request.FILES.get("archivo")
            )
        except ValidationError as error:
            mensajes = {campo: textos[0] for campo, textos in error.message_dict.items()}
            return JsonResponse({"errores": mensajes}, status=400)
        return render(request, "repositorio/_enviada.html", servicios.resumen(sesion), status=201)
