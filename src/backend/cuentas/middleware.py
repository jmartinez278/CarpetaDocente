"""Middleware de la sesión: cierre por inactividad (RN-025) y pantallas sin caché (RNF-015).

La regla vive en ``cuentas.servicios``; aquí solo se aplica a cada petición con sesión,
también en el panel (design.md de US-002, D1 y D3).
"""

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.views import redirect_to_login
from django.dispatch import receiver
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import add_never_cache_headers

from cuentas import servicios
from cuentas.acceso import es_htmx, redirigir

MARCA_DE_ACTIVIDAD = "ultima_actividad"
# La marca se reescribe solo si la guardada tiene 30 s o más: una pantalla que guarda por
# toque no escribe la sesión en cada petición. La sesión puede cerrarse hasta 30 s antes de
# los 60 minutos, nunca después (RN-025; design de US-030, D9).
RENOVACION_DE_LA_MARCA = 30
ETIQUETA_INACTIVIDAD = "inactividad"


@receiver(user_logged_in)
def iniciar_reloj_de_inactividad(sender, request, **kwargs):
    """Marca la actividad al autenticar: el POST de ingreso llega como anónimo y el middleware
    no lo ve, así que sin esto la sesión nueva no caducaría hasta otra petición (RN-025)."""
    request.session[MARCA_DE_ACTIVIDAD] = timezone.now().timestamp()


class InactividadMiddleware:
    """Termina la sesión tras 60 minutos sin peticiones y evita que se guarde en caché.

    - Vencida: ``logout()``, deja el aviso y redirige a ``/ingresar/``. Si era un GET,
      conserva la dirección pedida en ``next``; si no, no vuelve a un envío. Una petición de
      HTMX recibe ``HX-Redirect`` con la portada como ``next`` (US-006, D7).
    - Vigente: renueva la marca de la última actividad si la guardada tiene 30 s o más.
    - Toda respuesta a una petición con sesión lleva las cabeceras de no caché, para que
      el botón "atrás" no muestre la pantalla después de cerrar la sesión.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        ahora = timezone.now()
        if servicios.sesion_vencida(request.session.get(MARCA_DE_ACTIVIDAD), ahora):
            return self._cerrar_por_inactividad(request)
        self._renovar_marca(request, ahora)

        respuesta = self.get_response(request)
        add_never_cache_headers(respuesta)
        return respuesta

    def _renovar_marca(self, request, ahora):
        """Escribe la marca si falta o tiene 30 s o más; si no, no toca la sesión."""
        marca = request.session.get(MARCA_DE_ACTIVIDAD)
        if marca is None or ahora.timestamp() - marca >= RENOVACION_DE_LA_MARCA:
            request.session[MARCA_DE_ACTIVIDAD] = ahora.timestamp()

    def _cerrar_por_inactividad(self, request):
        logout(request)
        titulo, detalle = servicios.aviso_de_inactividad()
        messages.info(request, f"{titulo}\n\n{detalle}", extra_tags=ETIQUETA_INACTIVIDAD)
        destino = reverse("ingresar")
        if es_htmx(request):
            respuesta = redirigir(
                request, redirect_to_login(reverse("docente:portada"), destino).url
            )
        elif request.method == "GET":
            respuesta = redirect_to_login(request.get_full_path(), destino)
        else:
            respuesta = redirect(destino)
        add_never_cache_headers(respuesta)
        return respuesta
