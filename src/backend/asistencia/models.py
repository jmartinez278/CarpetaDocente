"""Modelos del módulo asistencia (documento 11, sección 3.5; design de US-030, D1).

Una ``Jornada`` es el día de clases de una sección; ``Asistencia`` guarda el estado de cada
estudiante en ella. La base de datos impide lo que el spec prohíbe: dos jornadas de la misma
sección y fecha, dos estados de un estudiante en una jornada, un estado fuera de los cuatro y
una nota sin Justificado.
"""

from django.db import models
from django.db.models import Q


class Jornada(models.Model):
    """Día de clases de una sección; se crea con el primer toque (D2).

    Que esté completa o incompleta se calcula, no se guarda (documento 11).
    ``creado_en`` guarda el primer toque: con ``Asistencia.actualizado_en`` da el tiempo de
    la toma (D1, datos para la tesis).
    """

    seccion = models.ForeignKey(
        "institucion.Seccion",
        on_delete=models.CASCADE,
        related_name="jornadas",
        verbose_name="sección",
    )
    fecha = models.DateField("fecha")
    registrado_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="jornadas_registradas",
        verbose_name="registrada por",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        db_table = "jornada"
        verbose_name = "jornada"
        verbose_name_plural = "jornadas"
        constraints = [
            models.UniqueConstraint(fields=["seccion", "fecha"], name="uq_jornada"),
        ]

    def __str__(self):
        return f"{self.seccion} – {self.fecha:%d-%m-%Y}"


class Asistencia(models.Model):
    """Estado de un estudiante en una jornada.

    ``estudiante`` es ``RESTRICT`` y no ``CASCADE`` como el documento 11: quitar o vaciar la
    lista se bloquea cuando hay asistencia (``institucion.servicios.ListaConRegistros``). Borrar
    la sección entera sí funciona: la asistencia cae en la misma cascada.
    """

    class Estado(models.TextChoices):
        ASISTIO = "ASISTIO", "Asistió"
        FALTO = "FALTO", "Faltó"
        TARDE = "TARDE", "Tarde"
        JUSTIFICADO = "JUSTIFICADO", "Justificado"

    jornada = models.ForeignKey(
        Jornada,
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="jornada",
    )
    estudiante = models.ForeignKey(
        "institucion.Estudiante",
        on_delete=models.RESTRICT,
        related_name="asistencias",
        verbose_name="estudiante",
    )
    estado = models.CharField("estado", max_length=12, choices=Estado)
    # Cadena vacía en vez de NULL, la convención de Django para texto (design D1).
    nota_justificacion = models.CharField(
        "nota de justificación", max_length=100, blank=True, default=""
    )
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        db_table = "asistencia"
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"
        constraints = [
            models.UniqueConstraint(fields=["jornada", "estudiante"], name="uq_asistencia"),
            models.CheckConstraint(
                condition=Q(estado__in=["ASISTIO", "FALTO", "TARDE", "JUSTIFICADO"]),
                name="ck_asistencia_estado",
            ),
            models.CheckConstraint(
                condition=Q(nota_justificacion="") | Q(estado="JUSTIFICADO"),
                name="ck_asistencia_nota",
            ),
        ]

    def __str__(self):
        return f"{self.estudiante} – {self.get_estado_display()}"
