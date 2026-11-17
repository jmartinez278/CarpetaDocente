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
    # Sin índice propio: lo cubre idx_sesion_autor_fecha, que empieza por la autora.
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
    # Texto transcrito del archivo, hasta 100 000 caracteres, y lo que recorre la búsqueda:
    # título, propósito y texto, normalizados (design de US-011, D1 y D4). Los dos los escribe
    # solo ``servicios``; pueden traer lo que la docente escribió (RN-015) y no van al registro
    # ni a los logs.
    texto = models.TextField("texto transcrito", blank=True, default="", db_default="")
    texto_busqueda = models.TextField("texto de búsqueda", blank=True, default="", db_default="")
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
            # Compartida solo si se aceptaron los términos (decisión 1, US-014). La que dejó de
            # compartirse conserva su fecha (US-011, D1).
            models.CheckConstraint(
                condition=Q(compartida=False) | Q(terminos_aceptados_en__isnull=False),
                name="ck_sesion_terminos",
            ),
        ]
        # idx_sesion_busqueda es del documento 11; idx_sesion_autor_fecha sirve a «Mis sesiones»
        # (US-011, D1). idx_sesion_titulo_trgm queda en la deuda.
        indexes = [
            models.Index(fields=["institucion", "grado", "area"], name="idx_sesion_busqueda"),
            models.Index(fields=["autor", "-creado_en"], name="idx_sesion_autor_fecha"),
        ]

    def __str__(self):
        return self.titulo

    @property
    def tipo_corto(self):
        """«PDF» o «Word», como lo nombran la tarjeta y la página."""
        return "PDF" if self.tipo_mime == TIPO_PDF else "Word"


class SesionVista(models.Model):
    """Una docente abrió la página de una sesión ajena: una fila por sesión y docente.

    De aquí sale «La vieron N colegas» y, con SESION_VISTA y SESION_DESCARGADA del registro, el
    uso del repositorio que mide la tesis (design de US-011, D1 y D6). Solo la crea
    ``servicios``.
    """

    # Sin índice propio: lo cubre uq_sesion_vista, que empieza por la sesión.
    sesion = models.ForeignKey(
        Sesion,
        on_delete=models.CASCADE,
        db_index=False,
        related_name="vistas",
        verbose_name="sesión",
    )
    # PROTECT, como el resto del modelo: las cuentas se desactivan, no se borran.
    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="sesiones_vistas",
        verbose_name="usuario",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        db_table = "sesion_vista"
        verbose_name = "vista de una sesión"
        verbose_name_plural = "vistas de sesiones"
        constraints = [
            models.UniqueConstraint(fields=["sesion", "usuario"], name="uq_sesion_vista"),
        ]

    def __str__(self):
        return f"{self.usuario_id} vio {self.sesion_id}"
