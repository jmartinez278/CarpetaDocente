"""Pantalla de inicio de cada rol y verificación de rol de las vistas (US-001).

Es lo único de control de acceso que entra en US-001: la matriz completa del
documento 08 y la denegación con registro son de US-004.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse

from cuentas.models import Usuario

_PANTALLA_DE_INICIO = {
    Usuario.Rol.DOCENTE: "docente:portada",
    Usuario.Rol.DIRECCION: "direccion:inicio",
    Usuario.Rol.ADMINISTRADOR: "admin:index",
}


def pantalla_de_inicio(usuario: Usuario) -> str:
    """Ruta de la pantalla a la que llega ``usuario`` al entrar, según su rol."""
    return reverse(_PANTALLA_DE_INICIO[usuario.rol])


class RolRequeridoMixin(LoginRequiredMixin):
    """Reserva una vista a un rol (spec inicio-sesion, "Pantalla de inicio reservada a su rol").

    Sin sesión, lleva a ``/ingresar/?next=…`` como ``LoginRequiredMixin``. Con otro
    rol, lleva a la pantalla de inicio de ese rol sin mostrar la vista pedida.
    """

    rol_requerido: str | None = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol != self.rol_requerido:
            return redirect(pantalla_de_inicio(request.user))
        return super().dispatch(request, *args, **kwargs)
