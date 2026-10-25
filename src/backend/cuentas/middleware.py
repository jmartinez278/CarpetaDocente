"""Middleware de la sesión: cierre por inactividad (RN-025) y pantallas sin caché (RNF-015).

La regla vive en ``cuentas.servicios``; aquí solo se aplica a cada petición con sesión,
también en el panel (design.md de US-002, D1 y D3).
"""

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import add_never_cache_headers

from cuentas import servicios

MARCA_DE_ACTIVIDAD = "ultima_actividad"
ETIQUETA_INACTIVIDAD = "inactividad"


class InactividadMiddleware:
    """Termina la sesión tras 60 minutos sin peticiones y evita que se guarde en caché.

    - Vencida: ``logout()``, deja el aviso y redirige a ``/ingresar/``. Si era un GET,
      conserva la dirección pedida en ``next``; si no, no vuelve a un envío.
    - Vigente: renueva la marca de la última actividad.
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
        request.session[MARCA_DE_ACTIVIDAD] = ahora.timestamp()

        respuesta = self.get_response(request)
        add_never_cache_headers(respuesta)
        return respuesta

    def _cerrar_por_inactividad(self, request):
        logout(request)
        titulo, detalle = servicios.aviso_de_inactividad()
        messages.info(request, f"{titulo}\n\n{detalle}", extra_tags=ETIQUETA_INACTIVIDAD)
        destino = reverse("ingresar")
        if request.method == "GET":
            respuesta = redirect_to_login(request.get_full_path(), destino)
        else:
            respuesta = redirect(destino)
        add_never_cache_headers(respuesta)
        return respuesta
