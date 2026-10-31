"""Modelos del módulo notas (documento 11, sección 3.5; design de US-029, D1).

``CompetenciaPeriodo`` es una marca: la competencia se desarrolló en la sección durante el
periodo. Desmarcar es borrar la fila. Que la sección y el periodo sean del mismo año lo
comprueba ``servicios``: la base no puede sin una FK compuesta.
"""

from django.db import models


class CompetenciaPeriodo(models.Model):
    """Competencia desarrollada por una sección en un periodo (RF-029, RN-005)."""

    seccion = models.ForeignKey(
        "institucion.Seccion",
        on_delete=models.CASCADE,
        related_name="competencias_periodo",
        verbose_name="sección",
    )
    periodo = models.ForeignKey(
        "institucion.Periodo",
        on_delete=models.CASCADE,
        related_name="competencias_periodo",
        verbose_name="periodo",
    )
    # RESTRICT: el catálogo no se borra (RN-023); una competencia marcada, menos.
    competencia = models.ForeignKey(
        "catalogo.Competencia",
        on_delete=models.RESTRICT,
        related_name="competencias_periodo",
        verbose_name="competencia",
    )

    class Meta:
        db_table = "competencia_periodo"
        verbose_name = "competencia del periodo"
        verbose_name_plural = "competencias del periodo"
        constraints = [
            # También es el índice para leer las marcas de una sección y periodo.
            models.UniqueConstraint(
                fields=["seccion", "periodo", "competencia"], name="uq_competencia_periodo"
            ),
        ]

    def __str__(self):
        return f"{self.competencia} – {self.seccion} – {self.periodo}"
