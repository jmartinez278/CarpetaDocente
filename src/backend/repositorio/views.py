"""Vistas de Sesiones (design de US-010, US-014 y EN-03, D7; de US-011, D5 a D7 y D10).

Solo leen la petición y llaman a ``repositorio.servicios``. Son del rol Docente, con o sin sección
(``RolRequeridoMixin``): la dirección y el Administrador van a su inicio sin registro de intento
(no es una ruta de sección, decisión 11) y una visita sin sesión, al ingreso; con ``HX-Request``,
por ``HX-Redirect``. El envío responde 201 con el fragmento del éxito o 400 con
``{"errores": {campo: mensaje}}``.

Las dos listas responden la pantalla completa o, con ``HX-Request``, el panel de resultados con
los contadores fuera de banda; con ``?pagina=N`` y ``HX-Request``, solo las tarjetas siguientes.
Una sesión que no está disponible para quien la pide responde 404 con la misma página en todos
los casos.
"""

from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.views import View

from cuentas.acceso import RolRequeridoMixin, es_htmx
from cuentas.models import Usuario
from repositorio import servicios

PLANTILLA_NO_DISPONIBLE = "repositorio/no_disponible.html"


class DocenteMixin(RolRequeridoMixin):
    rol_requerido = Usuario.Rol.DOCENTE


def no_disponible(request):
    """404 «La sesión ya no está disponible»: igual si no existe, si es ajena o de otra I.E."""
    return render(request, PLANTILLA_NO_DISPONIBLE, status=404)


def _responder_lista(request, contexto):
    """La pantalla, el panel de resultados (HTMX) o solo las tarjetas siguientes (D10)."""
    if es_htmx(request) and "pagina" in request.GET:
        respuesta = render(request, "repositorio/_tarjetas.html", contexto)
    elif es_htmx(request):
        respuesta = render(request, "repositorio/_resultados.html", contexto)
    else:
        contexto |= servicios.datos_del_formulario(request.user)
        respuesta = render(request, "repositorio/sesiones.html", contexto)
    patch_vary_headers(respuesta, ["HX-Request"])
    return respuesta


class SesionesView(DocenteMixin, View):
    """«Mis sesiones»: la pestaña con la que abre la pantalla Sesiones."""

    def get(self, request):
        contexto = {
            "pestana": "mis_sesiones",
            "pagina": servicios.mis_sesiones(request.user, request.GET.get("pagina")),
            "contadores": servicios.contadores(request.user),
        }
        return _responder_lista(request, contexto)


class RepositorioView(DocenteMixin, View):
    """«Repositorio»: las compartidas de la institución, con búsqueda y filtros en la dirección."""

    def get(self, request):
        q = request.GET.get("q", "")
        grado = request.GET.get("grado", "")
        contexto = {
            "pestana": "repositorio",
            "grados": servicios.GRADOS,
            "pagina": servicios.buscar_repositorio(
                request.user, q, grado, request.GET.get("area", ""), request.GET.get("pagina")
            ),
            "conteos": servicios.conteos_por_area(request.user, q, grado),
            "contadores": servicios.contadores(request.user),
        }
        return _responder_lista(request, contexto)


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


class SesionView(DocenteMixin, View):
    """La página de una sesión; la primera visita de una colega se cuenta (D6)."""

    def get(self, request, id_sesion):
        sesion = servicios.sesion_visible(request.user, id_sesion)
        if sesion is None:
            return no_disponible(request)
        servicios.registrar_vista(request.user, sesion)
        contexto = servicios.datos_de_la_pagina(request.user, sesion)
        return render(request, "repositorio/sesion.html", contexto)


class EntregarView(DocenteMixin, View):
    """«Descargar» o «Ver»: el enlace firmado de R2 o el archivo, sin caché (D7)."""

    modo = "descargar"

    def get(self, request, id_sesion):
        try:
            entrega = servicios.entregar_archivo(request.user, id_sesion, self.modo)
        except servicios.SesionNoDisponible:
            return no_disponible(request)
        if entrega.url is not None:
            respuesta = HttpResponseRedirect(entrega.url)
        else:
            respuesta = FileResponse(entrega.archivo, content_type=entrega.tipo_mime)
            respuesta["Content-Disposition"] = entrega.disposicion
            respuesta["X-Content-Type-Options"] = "nosniff"
        patch_cache_control(respuesta, no_store=True)
        return respuesta
