"""Modelos de exportaciones (US-024/025, design D5).

La plantilla del SIAGIE no se guarda (decisión 2, Ley 29733): de ella solo queda la
equivalencia de su sección con una sección de la I.E. Que la sección sea del año y del grado
guardados lo comprueba ``servicios``; la base no puede sin FK compuestas.
"""

from django.db import models


class EquivalenciaSeccion(models.Model):
    """Sección del SIAGIE (código y nombre) que corresponde a una sección de la I.E.

    Una por sección de la I.E. y una por sección del SIAGIE en el año y grado. ``nombre_siagie``
    se guarda normalizado. Borrar la equivalencia es la corrección «¿No es esta sección?» (D13).
    """

    seccion = models.OneToOneField(
        "institucion.Seccion",
        on_delete=models.CASCADE,
        related_name="equivalencia_siagie",
        verbose_name="sección de la I.E.",
    )
    anio_escolar = models.ForeignKey(
        "institucion.AnioEscolar",
        on_delete=models.CASCADE,
        related_name="equivalencias_siagie",
        verbose_name="año escolar",
    )
    grado = models.PositiveSmallIntegerField("grado")
    codigo_siagie = models.CharField("código de la sección en el SIAGIE", max_length=4)
    nombre_siagie = models.CharField("nombre de la sección en el SIAGIE", max_length=60)
    creado_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equivalencias_siagie",
        verbose_name="guardada por",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        db_table = "equivalencia_seccion"
        verbose_name = "equivalencia de sección del SIAGIE"
        verbose_name_plural = "equivalencias de sección del SIAGIE"
        ordering = ["anio_escolar", "grado", "nombre_siagie"]
        constraints = [
            # También es el índice con que se busca la equivalencia de una plantilla.
            models.UniqueConstraint(
                fields=["anio_escolar", "grado", "codigo_siagie", "nombre_siagie"],
                name="uq_equivalencia_seccion_siagie",
            ),
        ]

    def __str__(self):
        return f"{self.grado}.º {self.nombre_siagie} ({self.codigo_siagie}) → {self.seccion}"
