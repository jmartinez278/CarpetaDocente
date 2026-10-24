"""Registro de Usuario en el panel de administración (rol Administrador)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.db import transaction

from cuentas import servicios
from cuentas.models import Usuario


class FormularioAltaUsuario(AdminUserCreationForm):
    """Alta de usuarios desde el panel: rol e institución son parte del alta."""

    class Meta(AdminUserCreationForm.Meta):
        model = Usuario
        fields = ("username", "rol", "institucion")


class FormularioEdicionUsuario(UserChangeForm):
    """Edición de usuarios desde el panel."""

    class Meta(UserChangeForm.Meta):
        model = Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Pantallas del Administrador para las cuentas de usuario."""

    add_form = FormularioAltaUsuario
    form = FormularioEdicionUsuario

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "password1", "password2"),
            },
        ),
        ("Rol e institución", {"fields": ("rol", "institucion")}),
    )
    fieldsets = UserAdmin.fieldsets + (
        ("Rol e institución", {"fields": ("rol", "institucion")}),
        (
            "Control de la cuenta",
            {"fields": ("debe_cambiar_password", "intentos_fallidos", "bloqueado_hasta")},
        ),
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
    list_filter = ("rol", "institucion", "is_active", "is_staff")
    # El único camino para desbloquear es la acción, que deja constancia en el historial.
    readonly_fields = ("intentos_fallidos", "bloqueado_hasta")
    actions = ["desbloquear_cuenta"]

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
