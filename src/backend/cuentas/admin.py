"""Registro de Usuario en el panel de administración (rol Administrador)."""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction

from actividad.models import Operacion
from actividad.panel import AGREGAR, CAMPOS_DEL_PANEL, RegistraEnPanel
from cuentas import servicios
from cuentas.models import Usuario

ROLES_DEL_PANEL = (Usuario.Rol.DOCENTE, Usuario.Rol.DIRECCION)

# El sistema no usa grupos (RF-003 ya los esconde de la ficha): fuera del panel, para que
# no quede un camino de escritura sin registrar (US-008, D4).
if admin.site.is_registered(Group):
    admin.site.unregister(Group)


def _limitar_rol(campo):
    """Deja en el campo rol solo Docente y Dirección: el panel no asigna Administrador."""
    campo.choices = [
        ("", "---------"),
        *((valor, texto) for valor, texto in campo.choices if valor in ROLES_DEL_PANEL),
    ]


class FormularioAltaUsuario(UserCreationForm):
    """Alta de cuentas desde el panel (RF-003, R-11): todos los datos son obligatorios.

    Hereda de ``UserCreationForm`` y no de ``AdminUserCreationForm`` para que no se pueda crear
    una cuenta sin contraseña. Nombres, apellidos e institución son obligatorios aquí y no en el
    modelo, porque el Administrador de ``createsuperuser`` no los tiene.
    """

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("first_name", "last_name", "username", "rol", "institucion")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ("first_name", "last_name", "institucion"):
            self.fields[nombre].required = True
        _limitar_rol(self.fields["rol"])
        self.fields["username"].help_text = (
            "Inicial del primer nombre y primer apellido, en minúsculas, sin tildes ni ñ "
            "(ej. jperez). Si ya existe, se agrega un número (jperez2)."
        )

    def clean_username(self):
        """Usuario único sin distinguir mayúsculas y con el formato de R-11.

        El repetido se revisa primero: "JPerez" con "jperez" ya existente dice que el usuario
        existe, que es lo que pide el spec, y no solo que el formato falla.
        """
        usuario = self.cleaned_data["username"]
        if Usuario.objects.filter(username__iexact=usuario).exists():
            errores = [ValidationError("El usuario ya existe")]
            sugerido = servicios.sugerir_usuario(
                self.cleaned_data.get("first_name", ""), self.cleaned_data.get("last_name", "")
            )
            if sugerido:
                errores.append(ValidationError(f"Prueba con {sugerido}."))
            raise ValidationError(errores)
        if not servicios.usuario_valido(usuario):
            raise ValidationError(
                "Usa la inicial del primer nombre y el primer apellido, en minúsculas, "
                "sin tildes, ñ ni espacios (ej. jperez)."
            )
        return usuario


class FormularioEdicionUsuario(UserChangeForm):
    """Edición de usuarios desde el panel: el rol ofrece solo Docente y Dirección."""

    class Meta(UserChangeForm.Meta):
        model = Usuario

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "rol" in self.fields:
            _limitar_rol(self.fields["rol"])


@admin.register(Usuario)
class UsuarioAdmin(RegistraEnPanel, UserAdmin):
    """Pantallas del Administrador para las cuentas de usuario.

    Alta, edición, contraseña y desbloqueo quedan en el registro de actividad (US-008, D5).
    """

    add_form = FormularioAltaUsuario
    form = FormularioEdicionUsuario

    # Los nombres van antes que el usuario: la sugerencia de ``clean_username`` los necesita.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "rol",
                    "institucion",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    # Sin is_staff, is_superuser, grupos, permisos ni debe_cambiar_password (RF-003).
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "email")}),
        ("Rol e institución", {"fields": ("rol", "institucion")}),
        ("Estado", {"fields": ("is_active", "last_login", "date_joined")}),
        ("Control de la cuenta", {"fields": ("intentos_fallidos", "bloqueado_hasta")}),
    )
    list_display = (
        "username",
        "first_name",
        "last_name",
        "rol",
        "institucion",
        "is_active",
        "bloqueado_hasta",
    )
    list_filter = ("rol", "institucion", "is_active")
    actions = ["desbloquear_cuenta"]

    def get_readonly_fields(self, request, obj=None):
        """En la edición, el usuario y el control de la cuenta no se tocan.

        El único camino para desbloquear es la acción, que deja constancia en el historial. El
        rol de un Administrador tampoco se cambia: seguiría siendo superusuario con otro rol.
        """
        if obj is None:
            return ()
        solo_lectura = ("username", "intentos_fallidos", "bloqueado_hasta")
        if obj.rol == Usuario.Rol.ADMINISTRADOR:
            return (*solo_lectura, "rol")
        return solo_lectura

    def has_delete_permission(self, request, obj=None):
        """Las cuentas se desactivan, no se eliminan (RN-023): tampoco el superusuario."""
        return False

    def operacion_del_panel(self, request, obj, accion, campos):
        """Desmarcar "activo" es CUENTA_DESACTIVADA; reactivar, desbloquear y la contraseña,
        CUENTA_EDITADA con su campo (D3). Si al desactivar cambian otros campos, quedan las dos
        entradas, como en ``SeccionAdmin``. La contraseña también es ``password`` cuando se
        desactiva el ingreso con contraseña (``usable_password``)."""
        if accion == AGREGAR:
            return [(Operacion.CUENTA_CREADA, None)]
        if "is_active" in campos and not obj.is_active:
            otros = [campo for campo in campos if campo != "is_active"]
            operaciones = [(Operacion.CUENTA_DESACTIVADA, None)]
            if otros:
                operaciones.append((Operacion.CUENTA_EDITADA, {"campos": otros}))
            return operaciones
        return [(Operacion.CUENTA_EDITADA, {"campos": campos})]

    def campos_cambiados(self, form):
        if isinstance(form, AdminPasswordChangeForm):
            return ["password"]
        return super().campos_cambiados(form)

    def user_change_password(self, request, id, form_url=""):
        """La de Django no abre transacción: la contraseña y su entrada van juntas (D5)."""
        with transaction.atomic():
            return super().user_change_password(request, id, form_url)

    def response_add(self, request, obj, post_url_continue=None):
        """Tras el alta, el mensaje de éxito es "Cuenta creada" (RF-003)."""
        request._cuenta_creada = True
        return super().response_add(request, obj, post_url_continue)

    def message_user(self, request, message, level=messages.INFO, *args, **kwargs):
        """Cambia solo el mensaje de éxito del alta; los demás pasan como vienen."""
        if getattr(request, "_cuenta_creada", False) and level == messages.SUCCESS:
            message = "Cuenta creada"
        super().message_user(request, message, level, *args, **kwargs)

    @admin.action(description="Desbloquear cuenta", permissions=["change"])
    def desbloquear_cuenta(self, request, queryset):
        """Quita el bloqueo y los intentos (RN-024) y lo registra en el historial de cada cuenta.

        El desbloqueo y su registro van en una transacción por cuenta: sin registro, no hay
        desbloqueo.
        """
        desbloqueadas = sin_cambios = 0
        for usuario in queryset:
            with transaction.atomic():
                desbloqueada = servicios.desbloquear(usuario)
                if desbloqueada:
                    setattr(request, CAMPOS_DEL_PANEL, ["desbloqueo"])
                    self.log_change(request, usuario, "Cuenta desbloqueada.")
            if desbloqueada:
                desbloqueadas += 1
            else:
                sin_cambios += 1
        partes = []
        if desbloqueadas:
            partes.append(f"Cuentas desbloqueadas: {desbloqueadas}.")
        if sin_cambios:
            partes.append(f"Sin nada que desbloquear: {sin_cambios}.")
        self.message_user(request, " ".join(partes))
