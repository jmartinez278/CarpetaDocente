"""Registro de Usuario en el panel de administración (rol Administrador)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

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
    list_display = ("username", "first_name", "last_name", "rol", "institucion", "is_active")
    list_filter = ("rol", "institucion", "is_active", "is_staff")
