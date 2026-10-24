"""Backend de autenticación del sistema: el de Django más el bloqueo de RN-024."""

from asgiref.sync import sync_to_async
from django.contrib.auth.backends import ModelBackend

from cuentas import servicios
from cuentas.models import Usuario


class BackendConBloqueo(ModelBackend):
    """Autentica contra ``Usuario`` y aplica el bloqueo por intentos fallidos (RN-024).

    Es el único backend de ``AUTHENTICATION_BACKENDS``: todo camino de ingreso
    (``/ingresar/``, el panel o un ``authenticate()`` futuro) pasa por el bloqueo.
    La decisión la toma ``servicios.intentar_ingreso``; los permisos son los de
    ``ModelBackend``.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(Usuario.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            usuario = Usuario._default_manager.get_by_natural_key(username)
        except Usuario.DoesNotExist:
            # Calcula el hash igual que con una cuenta real, como ModelBackend (#20760):
            # el tiempo de respuesta no delata si la cuenta existe.
            Usuario().set_password(password)
            return None
        return usuario if servicios.intentar_ingreso(usuario, password) else None

    async def aauthenticate(self, request, username=None, password=None, **kwargs):
        # La de ModelBackend no llama a authenticate(): sin esto se saltaría el bloqueo.
        return await sync_to_async(self.authenticate)(
            request, username=username, password=password, **kwargs
        )
