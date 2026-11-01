"""Modelos del módulo notas (documento 11, sección 3.5; design de US-029 y US-020, D1).

``CompetenciaPeriodo`` es una marca: la competencia se desarrolló en la sección durante el
periodo. Desmarcar es borrar la fila. ``Calificacion`` es el nivel de logro de un estudiante
en una competencia y un periodo. Que la sección, el periodo y la competencia sean del mismo
año y de una columna de la hoja lo comprueba ``servicios``: la base no puede sin FK
compuestas.
"""

from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import GreaterThanOrEqual, LessThanOrEqual

# Escala de calificación de primaria (RN-001) y longitud de la conclusión (RN-002, D1).
CONCLUSION_MINIMA = 10
CONCLUSION_MAXIMA = 500


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


class Calificacion(models.Model):
    """Nivel de logro de un estudiante en una competencia y un periodo (RF-020, RF-021).

    ``estudiante`` es ``RESTRICT`` y no ``CASCADE`` como el documento 11: quitar o vaciar la
    lista se bloquea cuando hay notas (``institucion.servicios.ListaConRegistros``), como con
    la asistencia. La sección sale de ``estudiante.seccion`` (3FN).

    ``conclusion_descriptiva`` es cadena vacía en vez de NULL: obligatoria en B y C (de 10 a
    500 caracteres) y vacía en AD y A. El servicio da el error legible; el CHECK es la red.
    """

    class Nivel(models.TextChoices):
        AD = "AD", "AD"
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"

    estudiante = models.ForeignKey(
        "institucion.Estudiante",
        on_delete=models.RESTRICT,
        related_name="calificaciones",
        verbose_name="estudiante",
    )
    # RESTRICT: el catálogo no se borra (RN-023); una competencia con notas, menos.
    competencia = models.ForeignKey(
        "catalogo.Competencia",
        on_delete=models.RESTRICT,
        related_name="calificaciones",
        verbose_name="competencia",
    )
    periodo = models.ForeignKey(
        "institucion.Periodo",
        on_delete=models.CASCADE,
        related_name="calificaciones",
        verbose_name="periodo",
    )
    nivel = models.CharField("nivel", max_length=2, choices=Nivel)
    conclusion_descriptiva = models.TextField("conclusión descriptiva", blank=True, default="")
    registrado_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calificaciones_registradas",
        verbose_name="registrada por",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        db_table = "calificacion"
        verbose_name = "calificación"
        verbose_name_plural = "calificaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante", "competencia", "periodo"], name="uq_calificacion"
            ),
            models.CheckConstraint(
                condition=Q(nivel__in=["AD", "A", "B", "C"]), name="ck_calificacion_nivel"
            ),
            models.CheckConstraint(
                # Dos implicaciones: un nivel fuera de la escala solo lo rechaza el CHECK
                # del nivel, así cada restricción nombra una sola regla.
                condition=(
                    (~Q(nivel__in=["AD", "A"]) | Q(conclusion_descriptiva=""))
                    & (
                        ~Q(nivel__in=["B", "C"])
                        | Q(
                            GreaterThanOrEqual(Length("conclusion_descriptiva"), CONCLUSION_MINIMA),
                            LessThanOrEqual(Length("conclusion_descriptiva"), CONCLUSION_MAXIMA),
                        )
                    )
                ),
                name="ck_calificacion_conclusion",
            ),
        ]
        # Del documento 11: para ``tiene_notas`` y las notas faltantes de un periodo.
        indexes = [
            models.Index(fields=["periodo", "competencia"], name="idx_calificacion_periodo"),
        ]

    def __str__(self):
        return f"{self.estudiante} – {self.competencia} – {self.periodo}: {self.nivel}"
