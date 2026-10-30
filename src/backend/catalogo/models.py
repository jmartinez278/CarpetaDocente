"""Modelos del catálogo curricular (documento 11, sección 3.3; design de EN-06, D1).

Las áreas y competencias son las del registro de notas del SIAGIE y las carga la migración
``0002``. ``codigo_siagie`` es el único campo que no está en el documento 11. Ni ``orden``
del área ni el de la competencia son únicos: así el panel puede intercambiar dos órdenes.
"""

from django.db import models


class Area(models.Model):
    """Área (bloque) del registro de notas del SIAGIE; las transversales son bloques propios."""

    codigo_siagie = models.CharField("código SIAGIE", max_length=4, unique=True)
    nombre = models.CharField("nombre", max_length=80, unique=True)
    es_transversal = models.BooleanField("transversal", default=False)
    admite_exoneracion = models.BooleanField("admite exoneración", default=False)
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        db_table = "area"
        verbose_name = "área"
        verbose_name_plural = "áreas"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class Competencia(models.Model):
    """Competencia de un área, con el texto de la leyenda del SIAGIE (RN-023: no se borra)."""

    area = models.ForeignKey(
        Area,
        on_delete=models.RESTRICT,
        related_name="competencias",
        verbose_name="área",
    )
    nombre = models.CharField("nombre", max_length=250)
    orden = models.PositiveSmallIntegerField("orden", default=0)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        db_table = "competencia"
        verbose_name = "competencia"
        verbose_name_plural = "competencias"
        ordering = ["area__orden", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["area", "nombre"], name="uq_competencia"),
        ]

    def __str__(self):
        return self.nombre


class InstitucionArea(models.Model):
    """Si una institución trabaja un área (RN-007); una fila por institución y área (D4)."""

    institucion = models.ForeignKey(
        "institucion.Institucion",
        on_delete=models.CASCADE,
        related_name="areas",
        verbose_name="institución",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.RESTRICT,
        related_name="instituciones",
        verbose_name="área",
    )
    se_trabaja = models.BooleanField("se trabaja", default=True)

    class Meta:
        db_table = "institucion_area"
        verbose_name = "área de la institución"
        verbose_name_plural = "áreas de la institución"
        ordering = ["institucion", "area__orden"]
        constraints = [
            models.UniqueConstraint(fields=["institucion", "area"], name="uq_institucion_area"),
        ]

    def __str__(self):
        return f"{self.area} – {self.institucion}"
