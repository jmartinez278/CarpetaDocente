"""Modelos del módulo repositorio (documento 11, sección 3.4; design de US-010, US-014 y EN-03, D1).

``Sesion`` es una sesión de aprendizaje que una docente envía a la dirección y, si acepta los
términos, comparte en el repositorio. De su archivo se guardan la clave en el almacenamiento
``sesiones`` (``sesiones/<UUID>-<token>.pdf`` o ``.docx``), el nombre original, el tipo y el tamaño;
el archivo mismo vive en R2 o en ``media/`` (D2). Las reglas legibles las da ``servicios``;
los ``CHECK`` son la red.

Diferencias con el DDL del documento 11 (van a la deuda del cambio): suma ``estado`` y
``compartida``; ``terminos_aceptados_en`` solo si se comparte (decisión 1); sin
``application/msword`` y con tope de 4 MB; ``PROTECT`` en vez de ``RESTRICT``; todavía sin
``sesion_origen_id`` ni ``sesion_competencia``.

La sesión de referencia (US-018, D1) la carga el Administrador: sin autora, sin estado de envío
ni términos, con fuente y permiso de uso y un rango de grados (``grado`` a ``grado_hasta``). Se
guarda con ``compartida=True``, que para ella significa «está en el repositorio de su
institución». Diferencias con el documento 11 (deuda): ``grado_hasta``, ``estado`` vacío y los
``CHECK`` de la referencia.
"""

from django.db import models
from django.db.models import F, Q

# Tope del archivo (decisión 6): cabe en el cuerpo de una función de Vercel (4,5 MB).
TAMANO_MAXIMO = 4 * 1024 * 1024
TITULO_MAXIMO = 200
# Los dos tipos admitidos (D6), también en el CHECK.
TIPO_PDF = "application/pdf"
TIPO_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TIPOS_MIME = [TIPO_PDF, TIPO_DOCX]
# El origen de la sesión de referencia (US-018), también en los CHECK.
REFERENCIA = "REFERENCIA"


class Sesion(models.Model):
    """Sesión de aprendizaje enviada a la dirección (RF-010) y quizá compartida (RF-014)."""

    class Origen(models.TextChoices):
        # Cada historia agrega el suyo (y el CHECK): ADAPTADA (US-013) y ENTREGADA (US-017).
        PROPIA = "PROPIA", "Propia"
        REFERENCIA = REFERENCIA, "Material de referencia"

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
    # Sin índice propio: lo cubre idx_sesion_autor_fecha, que empieza por la autora. Vacía solo
    # en la sesión de referencia (ck_sesion_autor).
    autor = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
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
    # Rango de grados (US-018, D2): la sesión de una docente tiene los dos iguales.
    grado = models.SmallIntegerField("grado")
    # Nulo solo para las filas que escribe el código anterior a US-018 durante un despliegue: se lee
    # como ``grado``. Pasar a NOT NULL es una migración posterior, ya sin ese código en servicio.
    grado_hasta = models.SmallIntegerField("grado final", null=True, blank=True)
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
    # Cadena vacía en la sesión de referencia, que no se envía a la dirección (ck_sesion_estado).
    estado = models.CharField("estado", max_length=12, choices=Estado, blank=True)
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
    # Solo de la sesión de referencia (RN-020); vacíos en la de una docente. Como el texto, no
    # van al registro ni a los logs.
    fuente = models.CharField("fuente", max_length=300, blank=True, default="", db_default="")
    permiso_uso = models.CharField(
        "permiso de uso", max_length=300, blank=True, default="", db_default=""
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        db_table = "sesion"
        verbose_name = "sesión de aprendizaje"
        verbose_name_plural = "sesiones de aprendizaje"
        constraints = [
            models.UniqueConstraint(fields=["archivo_clave"], name="uq_sesion_archivo_clave"),
            models.CheckConstraint(
                condition=Q(grado__gte=1, grado__lte=F("grado_hasta"), grado_hasta__lte=6),
                name="ck_sesion_grado",
            ),
            # Solo la sesión de referencia tiene varios grados (US-018, decisión 4).
            models.CheckConstraint(
                condition=Q(origen=REFERENCIA) | Q(grado_hasta=F("grado")),
                name="ck_sesion_un_grado",
            ),
            models.CheckConstraint(
                condition=Q(origen__in=["PROPIA", REFERENCIA]),
                name="ck_sesion_origen",
            ),
            models.CheckConstraint(
                condition=Q(origen=REFERENCIA, estado="")
                | (~Q(origen=REFERENCIA) & Q(estado__in=["ENVIADA"])),
                name="ck_sesion_estado",
            ),
            # Sin autora solo la sesión de referencia, y ella siempre sin autora.
            models.CheckConstraint(
                condition=Q(origen=REFERENCIA, autor__isnull=True)
                | (~Q(origen=REFERENCIA) & Q(autor__isnull=False)),
                name="ck_sesion_autor",
            ),
            # La de referencia está en el repositorio, sin términos y con fuente y permiso
            # (RN-020). Que no sean solo espacios lo cuida ``servicios``.
            models.CheckConstraint(
                condition=~Q(origen=REFERENCIA)
                | (
                    Q(compartida=True, terminos_aceptados_en__isnull=True)
                    & ~Q(fuente="")
                    & ~Q(permiso_uso="")
                ),
                name="ck_sesion_referencia",
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
            # compartirse conserva su fecha (US-011, D1). La de referencia no tiene términos.
            models.CheckConstraint(
                condition=Q(compartida=False)
                | Q(terminos_aceptados_en__isnull=False)
                | Q(origen=REFERENCIA),
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
    def grados_texto(self):
        """«2.º grado» o, con varios, «3.º–5.º grado» (US-018, D1)."""
        if self.grado_hasta in (None, self.grado):
            return f"{self.grado}.º grado"
        return f"{self.grado}.º–{self.grado_hasta}.º grado"

    @property
    def tipo_corto(self):
        """«PDF» o «Word», como lo nombran la tarjeta y la página."""
        return "PDF" if self.tipo_mime == TIPO_PDF else "Word"


class _SoloReferencias(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(origen=Sesion.Origen.REFERENCIA)


class SesionReferencia(Sesion):
    """Las sesiones de referencia, y solo ellas: lo único que el panel ve de ``Sesion`` (D4)."""

    objects = _SoloReferencias()

    class Meta:
        proxy = True
        verbose_name = "sesión de referencia"
        verbose_name_plural = "sesiones de referencia"


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
