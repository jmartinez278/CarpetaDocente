"""Modelos del módulo repositorio (documento 11, sección 3.4; design de US-010, US-014 y EN-03, D1).

``Sesion`` es una sesión de aprendizaje que una docente envía a la dirección y, si acepta los
términos, comparte en el repositorio. De su archivo se guardan la clave en el almacenamiento
``sesiones`` (``sesiones/<UUID>-<token>.pdf`` o ``.docx``), el nombre original, el tipo y el tamaño;
el archivo mismo vive en R2 o en ``media/`` (D2). Las reglas legibles las da ``servicios``;
los ``CHECK`` son la red.

Diferencias con el DDL del documento 11 (van a la deuda del cambio): suma ``estado`` y
``compartida``; ``terminos_aceptados_en`` solo si se comparte (decisión 1); sin
``application/msword`` y con tope de 4 MB; ``PROTECT`` en vez de ``RESTRICT``; todavía sin
``sesion_origen_id``, ``fuente``, ``permiso_uso`` ni ``sesion_competencia``.
"""

from django.db import models
from django.db.models import Q

# Tope del archivo (decisión 6): cabe en el cuerpo de una función de Vercel (4,5 MB).
TAMANO_MAXIMO = 4 * 1024 * 1024
TITULO_MAXIMO = 200
# Los dos tipos admitidos (D6), también en el CHECK.
TIPO_PDF = "application/pdf"
TIPO_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TIPOS_MIME = [TIPO_PDF, TIPO_DOCX]


class Sesion(models.Model):
    """Sesión de aprendizaje enviada a la dirección (RF-010) y quizá compartida (RF-014)."""

    class Origen(models.TextChoices):
        # Cada historia agrega el suyo (y el CHECK): ADAPTADA (US-013), ENTREGADA (US-017)
        # y REFERENCIA (US-018).
        PROPIA = "PROPIA", "Propia"

    class Estado(models.TextChoices):
        # El bloque 2 agrega los de la revisión de la dirección (y el CHECK).
        ENVIADA = "ENVIADA", "Enviada a la dirección"

    class TipoMime(models.TextChoices):
        PDF = TIPO_PDF, "PDF"
        DOCX = TIPO_DOCX, "Word (.docx)"

    # Sin default: lo genera el navegador al abrir el formulario, para que un reintento no
    # duplique la sesión (D5).
    id = models.UUIDField("id", primary_key=True)
    # PROTECT en las cuatro FK: las cuentas se desactivan, no se borran, y una sesión no
    # desaparece porque se borre su autora, su área o su institución.
    # Sin índice propio: lo cubre idx_sesion_busqueda, que empieza por la institución.
    institucion = models.ForeignKey(
        "institucion.Institucion",
        on_delete=models.PROTECT,
        db_index=False,
        related_name="sesiones",
        verbose_name="institución",
    )
    # Sin índice propio: es idx_sesion_autor, con el nombre del documento 11.
    autor = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        db_index=False,
        related_name="sesiones_de_autoria",
        verbose_name="autora",
    )
    subido_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="sesiones_subidas",
        verbose_name="subida por",
    )
    grado = models.SmallIntegerField("grado")
    area = models.ForeignKey(
        "catalogo.Area",
        on_delete=models.PROTECT,
        related_name="sesiones",
        verbose_name="área",
    )
    titulo = models.CharField("título", max_length=TITULO_MAXIMO)
    # Cadena vacía en vez de NULL, como en US-030.
    proposito = models.TextField("propósito", blank=True, default="")
    origen = models.CharField("origen", max_length=12, choices=Origen)
    estado = models.CharField("estado", max_length=12, choices=Estado)
    compartida = models.BooleanField("compartida en el repositorio", default=False)
    archivo_clave = models.CharField("clave del archivo", max_length=300)
    archivo_nombre = models.CharField("nombre original del archivo", max_length=255)
    tipo_mime = models.CharField("tipo del archivo", max_length=100, choices=TipoMime)
    tamano_bytes = models.IntegerField("tamaño en bytes")
    terminos_aceptados_en = models.DateTimeField("términos aceptados en", null=True, blank=True)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        db_table = "sesion"
        verbose_name = "sesión de aprendizaje"
        verbose_name_plural = "sesiones de aprendizaje"
        constraints = [
            models.UniqueConstraint(fields=["archivo_clave"], name="uq_sesion_archivo_clave"),
            models.CheckConstraint(condition=Q(grado__gte=1, grado__lte=6), name="ck_sesion_grado"),
            models.CheckConstraint(
                condition=Q(origen__in=["PROPIA"]),
                name="ck_sesion_origen",
            ),
            models.CheckConstraint(
                condition=Q(estado__in=["ENVIADA"]),
                name="ck_sesion_estado",
            ),
            models.CheckConstraint(
                condition=Q(tipo_mime__in=TIPOS_MIME),
                name="ck_sesion_tipo_mime",
            ),
            models.CheckConstraint(
                condition=Q(tamano_bytes__gte=1, tamano_bytes__lte=TAMANO_MAXIMO),
                name="ck_sesion_tamano",
            ),
            models.CheckConstraint(condition=~Q(titulo=""), name="ck_sesion_titulo"),
            # Compartida si y solo si se aceptaron los términos (decisión 1, US-014).
            models.CheckConstraint(
                condition=(
                    Q(compartida=True, terminos_aceptados_en__isnull=False)
                    | Q(compartida=False, terminos_aceptados_en__isnull=True)
                ),
                name="ck_sesion_terminos",
            ),
        ]
        # Del documento 11; idx_sesion_titulo_trgm llega con la búsqueda (US-011).
        indexes = [
            models.Index(fields=["institucion", "grado", "area"], name="idx_sesion_busqueda"),
            models.Index(fields=["autor"], name="idx_sesion_autor"),
        ]

    def __str__(self):
        return self.titulo
