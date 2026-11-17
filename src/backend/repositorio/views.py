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

Eliminar, compartir y dejar de compartir son formularios normales (``POST``, PRG con
``django.contrib.messages``): 303 a «Mis sesiones» o a la página con su Mensaje; 403 con la página
y «Solo el autor puede eliminar esta sesión» si es ajena y visible; 400 con la página si se
comparte sin aceptar los términos (D8).
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.utils.http import urlencode
from django.views import View

from cuentas.acceso import RolRequeridoMixin, es_htmx
from cuentas.models import Usuario
from repositorio import servicios

PLANTILLA_NO_DISPONIBLE = "repositorio/no_disponible.html"
# Etiqueta de los Mensajes de Sesiones: solo los muestran sus plantillas.
ETIQUETA_MENSAJE = "sesiones"


class DocenteMixin(RolRequeridoMixin):
    rol_requerido = Usuario.Rol.DOCENTE


def no_disponible(request):
    """404 «La sesión ya no está disponible»: igual si no existe, si es ajena o de otra I.E."""
    return render(request, PLANTILLA_NO_DISPONIBLE, status=404)


def _url_repositorio(q="", grado=None, area=None, pagina=None):
    """La dirección del repositorio con esa búsqueda, ese grado y esa área (los vacíos no van)."""
    parametros = [("q", q), ("grado", grado), ("area", area), ("pagina", pagina)]
    consulta = urlencode([(nombre, valor) for nombre, valor in parametros if valor])
    base = reverse("sesiones:repositorio")
    return f"{base}?{consulta}" if consulta else base


def _enlaces_de_la_lista(contexto):
    """Las direcciones que dibujan las listas: filtros, filtros activos y «Ver más» (D10).

    Cada filtro es un enlace con la dirección ya armada, así que funciona sin JavaScript; tocar
    el grado o el área elegidos los quita. ``cuenta`` es cuántos filtros hay puestos.
    """
    pagina = contexto["pagina"]
    if contexto["pestana"] == "mis_sesiones":
        mas = f"{reverse('sesiones:inicio')}?{urlencode({'pagina': pagina.pagina + 1})}"
        return {"cuenta": 0, "mas": mas}
    q, grado, area = pagina.q, pagina.grado, pagina.area.pk if pagina.area else None
    conteos = contexto["conteos"]
    areas = [("", "Todas las áreas", conteos.total, _url_repositorio(q, grado), area is None)]
    areas += [
        (
            a.pk,
            a.nombre,
            n,
            _url_repositorio(q, grado, None if a.pk == area else a.pk),
            a.pk == area,
        )
        for a, n in conteos.areas
    ]
    return {
        "cuenta": sum(bool(filtro) for filtro in (q, grado, area)),
        "grados": [
            (g, etiqueta, _url_repositorio(q, None if g == grado else g, area), g == grado)
            for g, etiqueta in contexto["grados"]
        ],
        "areas": areas,
        "sin_q": _url_repositorio("", grado, area),
        "sin_grado": _url_repositorio(q, None, area),
        "sin_area": _url_repositorio(q, grado, None),
        "limpiar": _url_repositorio(),
        "mas": _url_repositorio(q, grado, area, pagina.pagina + 1),
    }


def _plantilla_htmx(request, contexto):
    """La plantilla de una petición de HTMX: tarjetas, resultados con sus filtros o el panel."""
    if "pagina" in request.GET:
        return "repositorio/_tarjetas.html"
    # Buscar y filtrar piden solo #resultados; las pestañas y el envío piden todo el panel.
    if request.headers.get("HX-Target") == "resultados" and contexto["pestana"] == "repositorio":
        return "repositorio/_actualizacion.html"
    return "repositorio/_resultados.html"


def _responder_lista(request, contexto):
    """La pantalla, el panel, los resultados (HTMX) o solo las tarjetas siguientes (D10)."""
    contexto["enlaces"] = _enlaces_de_la_lista(contexto)
    # «Atrás» con HTMX pide la página entera aunque lleve HX-Request: nunca un fragmento.
    if es_htmx(request) and not request.headers.get("HX-History-Restore-Request"):
        respuesta = render(request, _plantilla_htmx(request, contexto), contexto)
    else:
        contexto |= servicios.datos_del_formulario(request.user)
        respuesta = render(request, "repositorio/sesiones.html", contexto)
    patch_vary_headers(respuesta, ["HX-Request", "HX-Target"])
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
        try:
            servicios.registrar_vista(request.user, sesion)
        except servicios.SesionNoDisponible:
            return no_disponible(request)
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


class _EscrituraDeLaAutoraView(DocenteMixin, View):
    """Base de eliminar, compartir y dejar de compartir: solo ``POST`` (D8, D10)."""

    http_method_names = ["post"]
    mensaje = ""

    def escribir(self, request, id_sesion):
        raise NotImplementedError

    def destino(self, id_sesion):
        return reverse("sesiones:detalle", args=[id_sesion])

    def post(self, request, id_sesion):
        try:
            self.escribir(request, id_sesion)
        except servicios.SesionNoDisponible:
            return no_disponible(request)
        except servicios.SoloLaAutora as error:
            return _pagina_con_error(request, id_sesion, str(error), status=403)
        except ValidationError as error:
            return _pagina_con_error(request, id_sesion, error.messages[0], status=400)
        messages.success(request, self.mensaje, extra_tags=ETIQUETA_MENSAJE)
        return HttpResponseRedirect(self.destino(id_sesion), status=303)


def _pagina_con_error(request, id_sesion, error, status):
    """La página de la sesión con el Mensaje de error; si dejó de verse, «no disponible»."""
    sesion = servicios.sesion_visible(request.user, id_sesion)
    if sesion is None:
        return no_disponible(request)
    contexto = servicios.datos_de_la_pagina(request.user, sesion) | {"error": error}
    return render(request, "repositorio/sesion.html", contexto, status=status)


class EliminarView(_EscrituraDeLaAutoraView):
    """Elimina la sesión propia y lleva a «Mis sesiones» con «Sesión eliminada»."""

    mensaje = "Sesión eliminada"

    def escribir(self, request, id_sesion):
        servicios.eliminar_sesion(request.user, id_sesion, request.path)

    def destino(self, id_sesion):
        return reverse("sesiones:inicio")


class CompartirView(_EscrituraDeLaAutoraView):
    """Comparte la sesión propia si llega la aceptación de los términos."""

    mensaje = "Sesión compartida en el repositorio"

    def escribir(self, request, id_sesion):
        acepta = servicios.casilla_marcada(request.POST.get("acepta_terminos"))
        servicios.compartir_sesion(request.user, id_sesion, acepta, request.path)


class DejarDeCompartirView(_EscrituraDeLaAutoraView):
    """Saca la sesión propia del repositorio, sin confirmación."""

    mensaje = "Dejaste de compartir la sesión"

    def escribir(self, request, id_sesion):
        servicios.dejar_de_compartir(request.user, id_sesion, request.path)
