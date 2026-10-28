"""Modelos del módulo institucion (documento 11, secciones 3.1 y 3.2).

``servicios`` importa estos modelos; por eso los métodos lo importan dentro de su cuerpo.
"""

from django.db import models, transaction
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


class AnioEscolar(models.Model):
    """Año escolar de una institución (documento 11, sección 3.1).

    Sin los campos de cierre de RF-009 ni los periodos de RF-028 (design de US-005, D1).
    Una institución tiene a lo sumo un año ABIERTO, y lo exige la base de datos (D5).
    """

    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        CERRADO = "CERRADO", "Cerrado"

    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.PROTECT,
        related_name="anios_escolares",
        verbose_name="institución",
    )
    anio = models.PositiveSmallIntegerField("año")
    estado = models.CharField("estado", max_length=10, choices=Estado, default=Estado.ABIERTO)

    class Meta:
        db_table = "anio_escolar"
        verbose_name = "año escolar"
        verbose_name_plural = "años escolares"
        ordering = ["-anio"]
        constraints = [
            models.UniqueConstraint(fields=["institucion", "anio"], name="uq_anio_escolar"),
            models.UniqueConstraint(
                fields=["institucion"],
                condition=Q(estado="ABIERTO"),
                name="uq_anio_escolar_abierto",
                violation_error_message="La institución ya tiene un año escolar abierto.",
            ),
            models.CheckConstraint(
                condition=Q(anio__gte=2026, anio__lte=2100), name="ck_anio_escolar_anio"
            ),
            models.CheckConstraint(
                condition=Q(estado__in=["ABIERTO", "CERRADO"]), name="ck_anio_escolar_estado"
            ),
        ]

    def __str__(self):
        return f"{self.anio} ({self.get_estado_display().lower()}) – {self.institucion}"


class Seccion(models.Model):
    """Sección de un año escolar, con un solo grado y su docente de aula (doc. 11, 3.2).

    Una sección tiene un docente; un docente puede tener varias secciones.
    """

    anio_escolar = models.ForeignKey(
        AnioEscolar,
        on_delete=models.CASCADE,
        related_name="secciones",
        verbose_name="año escolar",
    )
    grado = models.PositiveSmallIntegerField("grado")
    nombre = models.CharField("nombre", max_length=20)
    docente = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="secciones",
        verbose_name="docente de aula",
    )

    class Meta:
        db_table = "seccion"
        verbose_name = "sección"
        verbose_name_plural = "secciones"
        ordering = ["grado", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["anio_escolar", "grado", "nombre"], name="uq_seccion"),
            models.CheckConstraint(
                condition=Q(grado__gte=1, grado__lte=6), name="ck_seccion_grado"
            ),
        ]

    def __str__(self):
        from institucion import servicios

        return servicios.texto_seccion(self)

    def save(self, *args, **kwargs):
        """Repite la regla de D3 en todo guardado, no solo en el formulario del panel."""
        from institucion import servicios

        with transaction.atomic():
            servicios.validar_asignacion(self, bloquear=True)
            super().save(*args, **kwargs)

    def clean(self):
        """La regla del docente de aula, con su mensaje en el campo (design de US-005, D3)."""
        from institucion import servicios

        servicios.validar_asignacion(self)


class Estudiante(models.Model):
    """Estudiante de una sección: solo apellidos y nombres, en mayúsculas (US-006, D1; RN-015).

    ``save()`` guarda la forma normalizada, así que ``uq_estudiante`` compara siempre lo
    guardado. ``QuerySet.update()`` y ``bulk_update`` no pasan por ``save()``; ``bulk_create``
    solo lo usa ``servicios.importar_lista``, con filas ya normalizadas.

    Las tablas futuras con FK a estudiante (calificación, asistencia, exoneración) usarán
    ``models.RESTRICT`` y no ``CASCADE`` como el documento 11: así quitar o vaciar la lista
    se bloquea solo cuando hay registros (``servicios.ListaConRegistros``).
    """

    seccion = models.ForeignKey(
        Seccion,
        on_delete=models.CASCADE,
        related_name="estudiantes",
        verbose_name="sección",
    )
    apellidos = models.CharField("apellidos", max_length=120)
    nombres = models.CharField("nombres", max_length=120)

    class Meta:
        db_table = "estudiante"
        verbose_name = "estudiante"
        verbose_name_plural = "estudiantes"
        constraints = [
            models.UniqueConstraint(
                fields=["seccion", "apellidos", "nombres"],
                name="uq_estudiante",
                violation_error_message="Este estudiante ya está en la lista",
            ),
        ]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    def save(self, *args, **kwargs):
        self._normalizar()
        super().save(*args, **kwargs)

    def clean(self):
        """Normaliza antes de que ``full_clean`` valide ``uq_estudiante``."""
        self._normalizar()

    def _normalizar(self):
        from institucion import servicios

        self.apellidos = servicios.normalizar_nombre(self.apellidos)
        self.nombres = servicios.normalizar_nombre(self.nombres)
