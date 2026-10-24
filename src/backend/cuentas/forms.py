"""Formularios del módulo cuentas."""

from django.contrib.auth.forms import AuthenticationForm

# Primera línea del mensaje de RF-001 (documento 06, V_1_5_0). La segunda la pone la
# plantilla, para darle otro peso sin HTML dentro del mensaje (DESIGN.md, R-27).
MENSAJE_RECHAZO = "Usuario o contraseña incorrectos, o cuenta inactiva"


class FormularioIngreso(AuthenticationForm):
    """Ingreso con usuario y contraseña (RF-001).

    Cualquier rechazo (contraseña incorrecta, usuario inexistente, cuenta inactiva o
    bloqueada) da el mismo mensaje: no revela qué falló. Con un campo vacío no se
    llama a ``authenticate()``, así que no se cuenta un intento (RN-024).
    """

    error_messages = {
        "invalid_login": MENSAJE_RECHAZO,
        "inactive": MENSAJE_RECHAZO,
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        usuario = self.fields["username"]
        usuario.label = "Usuario"
        usuario.error_messages["required"] = "Ingresa tu usuario."
        contrasena = self.fields["password"]
        contrasena.label = "Contraseña"
        contrasena.error_messages["required"] = "Ingresa tu contraseña."
