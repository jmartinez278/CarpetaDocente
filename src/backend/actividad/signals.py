"""Inicio y cierre de sesión en el registro de actividad (design de US-008, D4).

Conectados en ``ActividadConfig.ready()``. Cada receptor abre su ``atomic()``: en el ingreso
queda anidado en el de ``IngresarView.form_valid`` (la entrada va con ``last_login``); el cierre
no tiene otra escritura que acompañar.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import transaction
from django.dispatch import receiver

from actividad.models import Operacion
from actividad.servicios import registrar

# ``InactividadMiddleware`` pone esta marca en ``request`` antes de ``logout()``.
MARCA_INACTIVIDAD = "_cierre_por_inactividad"


@receiver(user_logged_in, dispatch_uid="actividad_inicio_sesion")
def registrar_inicio_sesion(sender, request, user, **kwargs):
    with transaction.atomic():
        registrar(user, Operacion.INICIO_SESION, entidad="usuario", entidad_id=user)


@receiver(user_logged_out, dispatch_uid="actividad_cierre_sesion")
def registrar_cierre_sesion(sender, request, user, **kwargs):
    if user is None:  # "Cerrar sesión" sin sesión: no hay sesión que cerrar
        return
    motivo = "inactividad" if getattr(request, MARCA_INACTIVIDAD, False) else "boton"
    with transaction.atomic():
        registrar(
            user,
            Operacion.CIERRE_SESION,
            entidad="usuario",
            entidad_id=user,
            detalle={"motivo": motivo},
        )
