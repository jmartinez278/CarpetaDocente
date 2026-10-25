"""Modelos del módulo cuentas (documento 11, sección 3.2; documento 08)."""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Q


class GestorUsuarios(UserManager):
    """Gestor de usuarios: todo superusuario tiene el rol ADMINISTRADOR."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Crea un superusuario con rol ADMINISTRADOR; rechaza cualquier otro rol."""
        extra_fields.setdefault("rol", Usuario.Rol.ADMINISTRADOR)
        if extra_fields["rol"] != Usuario.Rol.ADMINISTRADOR:
            raise ValueError("El superusuario debe tener rol=ADMINISTRADOR.")
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Cuenta de usuario del sistema, con su rol y su institución educativa.

    La contraseña se guarda solo como hash (RNF-012). Los campos de control de
    cuenta los usan RF-007 (contraseña temporal) y RN-024 (bloqueo por intentos).
    """

    class Rol(models.TextChoices):
        """Roles del documento 08."""

        DOCENTE = "DOCENTE", "Docente"
        DIRECCION = "DIRECCION", "Dirección"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    rol = models.CharField("rol", max_length=15, choices=Rol)
    institucion = models.ForeignKey(
        "institucion.Institucion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="institución",
    )
    debe_cambiar_password = models.BooleanField("debe cambiar la contraseña", default=False)
    intentos_fallidos = models.SmallIntegerField("intentos fallidos", default=0)
    bloqueado_hasta = models.DateTimeField("bloqueado hasta", null=True, blank=True)

    objects = GestorUsuarios()

    @classmethod
    def normalize_username(cls, username):
        """Además de la normalización Unicode de Django, el usuario va en minúsculas (D7)."""
        return super().normalize_username(username).lower()

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            models.CheckConstraint(
                condition=Q(rol__in=["DOCENTE", "DIRECCION", "ADMINISTRADOR"]),
                name="ck_usuario_rol",
            ),
            # Solo el Administrador puede no pertenecer a una institución.
            models.CheckConstraint(
                condition=Q(rol="ADMINISTRADOR") | Q(institucion__isnull=False),
                name="ck_usuario_institucion",
                violation_error_message="Docente y Dirección deben pertenecer a una institución.",
            ),
        ]
