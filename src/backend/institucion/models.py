"""Modelos del módulo institucion (documento 11, sección 3.1)."""

from django.db import models
from django.db.models import Q


class Institucion(models.Model):
    """Institución educativa. Existe desde el inicio para atender a más de una I.E."""

    class OrganizacionPeriodos(models.TextChoices):
        """Forma en que la I.E. divide el año escolar (RN-006)."""

        BIMESTRE = "BIMESTRE", "Bimestre"
        TRIMESTRE = "TRIMESTRE", "Trimestre"

    nombre = models.CharField("nombre", max_length=200)
    codigo_modular = models.CharField(
        "código modular", max_length=20, unique=True, null=True, blank=True
    )
    # Nullable como en el DDL del documento 11: NULL = aún no definida [DATO I.E. PENDIENTE].
    organizacion_periodos = models.CharField(  # noqa: DJ001
        "organización de periodos",
        max_length=10,
        choices=OrganizacionPeriodos,
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        db_table = "institucion"
        verbose_name = "institución"
        verbose_name_plural = "instituciones"
        constraints = [
            models.CheckConstraint(
                condition=Q(organizacion_periodos__in=["BIMESTRE", "TRIMESTRE"])
                | Q(organizacion_periodos__isnull=True),
                name="ck_institucion_organizacion_periodos",
            ),
        ]

    def __str__(self):
        return self.nombre
