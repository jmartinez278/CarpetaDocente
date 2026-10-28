"""Reglas de negocio del módulo institucion (documento 12: capa de servicios)."""

import unicodedata
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Count, ProtectedError, Q, RestrictedError

from cuentas.models import Usuario
from institucion.models import AnioEscolar, Estudiante, Seccion

SECCION_OCUPADA = "La sección ya tiene un docente asignado"
SIN_SECCION = "Tu sección aparecerá cuando el administrador la asigne."
GRADOS = range(1, 7)
NOMBRES_SECCION = ("A", "B", "C", "D")
DOCENTE_NO_ELEGIBLE = "Elige una docente activa de la institución del año escolar."
MAX_ESTUDIANTES_LISTA = 60


def normalizar_nombre(texto):
    """Apellidos o nombres en mayúsculas y sin espacios de más (US-006, D1).

    ``split()`` también quita los espacios duros (U+00A0) que trae Excel; ``upper()``
    conserva tildes y Ñ.
    """
    return unicodedata.normalize("NFC", " ".join(texto.split()).upper())


@dataclass(frozen=True)
class ErrorLista:
    """Error de la lista pegada: las líneas afectadas, su motivo y cómo corregirlo (D3)."""

    lineas: tuple
    motivo: str
    ayuda: str

    @property
    def titulo(self):
        """ "Línea 7: motivo", "Líneas 4 y 12: motivo" o el motivo solo (sin líneas)."""
        if not self.lineas:
            return self.motivo
        if len(self.lineas) == 1:
            return f"Línea {self.lineas[0]}: {self.motivo}"
        *primeras, ultima = self.lineas
        return f"Líneas {', '.join(map(str, primeras))} y {ultima}: {self.motivo}"


def _error_de_formato(linea):
    """Motivo y ayuda de una línea con texto mal formada, o ``None`` si está bien (D3, 4)."""
    if "\t" in linea:
        return (
            "pega solo la columna de apellidos y nombres",
            "Quita las demás columnas de esa línea.",
        )
    comas = linea.count(",")
    if comas == 0:
        return (
            "falta la coma entre apellidos y nombres",
            "Separa los apellidos de los nombres con una coma.",
        )
    if comas > 1:
        return "tiene más de una coma", "Deja una sola coma, entre apellidos y nombres."
    apellidos, nombres = (normalizar_nombre(lado) for lado in linea.split(","))
    ayuda = "Escribe apellidos y nombres separados por una coma."
    if not apellidos:
        return "faltan los apellidos", ayuda
    if not nombres:
        return "faltan los nombres", ayuda
    return None


def leer_lista_pegada(texto):
    """Lee el texto pegado: devuelve ``(filas, errores)`` sin tocar la base de datos (D3).

    Las filas son ``(linea, apellidos, nombres)`` ya normalizadas. La línea se numera por su
    posición en el texto, contando las líneas en blanco, que se ignoran. Con más de 60 líneas
    con texto devuelve solo ese error. Una línea con error muestra un solo motivo.
    """
    # Sin ``splitlines()``: también corta en U+2028 y desfasaría la numeración.
    lineas = texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    con_texto = [(numero, linea) for numero, linea in enumerate(lineas, start=1) if linea.strip()]
    if len(con_texto) > MAX_ESTUDIANTES_LISTA:
        error = ErrorLista(
            (),
            f"La lista tiene {len(con_texto)} líneas; el máximo es {MAX_ESTUDIANTES_LISTA}",
            "Pega solo los estudiantes de tu sección.",
        )
        return [], [error]
    filas, errores = [], []
    for numero, linea in con_texto:
        problema = _error_de_formato(linea)
        if problema is None:
            apellidos, nombres = (normalizar_nombre(lado) for lado in linea.split(","))
            filas.append((numero, apellidos, nombres))
        else:
            errores.append(ErrorLista((numero,), *problema))
    return filas, errores


def texto_seccion(seccion):
    """Texto de una sección: "2.º grado, sección A", con el ordinal º (U+00BA) (US-005, D2)."""
    return f"{seccion.grado}.º grado, sección {seccion.nombre}"


def texto_seccion_corto(seccion):
    """Texto corto para el título del diálogo: "2.º A" (US-006, D2)."""
    return f"{seccion.grado}.º {seccion.nombre}"


def secciones_docente(usuario):
    """Secciones del docente en el año ABIERTO, por grado y nombre (US-006, D2)."""
    return Seccion.objects.filter(
        docente=usuario, anio_escolar__estado=AnioEscolar.Estado.ABIERTO
    ).order_by("grado", "nombre")


def seccion_unica(usuario):
    """La sección del año ABIERTO si el docente tiene exactamente una, con su cantidad.

    La cantidad de estudiantes va en ``cantidad_estudiantes``. Con varias secciones o con
    ninguna devuelve ``None``: la portada no ofrece entrada a la lista (US-006, D2).
    """
    secciones = list(
        secciones_docente(usuario).annotate(cantidad_estudiantes=Count("estudiantes"))[:2]
    )
    return secciones[0] if len(secciones) == 1 else None


def texto_secciones_docente(usuario):
    """Línea de la portada con las secciones del docente en el año ABIERTO (US-005, D2).

    Van ordenadas por grado y nombre y unidas con " · ". Sin ninguna, avisa que aparecerá.
    """
    secciones = secciones_docente(usuario)
    if not secciones:
        return SIN_SECCION
    return " · ".join(texto_seccion(seccion) for seccion in secciones)


def docentes_elegibles(seccion):
    """Cuentas que se ofrecen como docente de aula de una sección guardada (US-005, D4).

    Las activas con rol Docente de la institución del año, más el docente que la sección
    ya tiene guardado, aunque esté inactivo: así su ficha se guarda o se vacía sin error.
    """
    elegibles = Q(
        rol=Usuario.Rol.DOCENTE,
        is_active=True,
        institucion_id=seccion.anio_escolar.institucion_id,
    )
    if seccion.docente_id is not None:
        elegibles |= Q(pk=seccion.docente_id)
    return Usuario.objects.filter(elegibles).order_by("last_name", "first_name")


def validar_asignacion(seccion, *, bloquear=False):
    """Valida el docente de aula de una sección contra el que está guardado (RF-005).

    - Si el docente no cambia (aunque ya esté inactivo) o el campo queda vacío, acepta.
    - Si la sección ya tiene otro docente guardado, rechaza con ``SECCION_OCUPADA``: el
      cambio de sección se hace en dos pasos, primero vaciando la sección (design, D3).
    - Si la sección está vacía, el docente nuevo debe ser una cuenta activa con rol
      Docente de la institución del año escolar, según la base de datos y no según el objeto.

    ``bloquear`` lee la fila guardada con ``select_for_update`` (requiere una transacción):
    así, de dos Administradores que asignan a la vez, el segundo recibe el error.
    ``QuerySet.update()`` y ``bulk_update`` no pasan por aquí: no se usan sobre ``Seccion``.
    """
    if seccion.docente_id is None or seccion.anio_escolar_id is None:
        return
    guardado = None
    if seccion.pk is not None:
        filas = Seccion.objects.filter(pk=seccion.pk)
        if bloquear:
            filas = filas.select_for_update()
        guardado = filas.values_list("docente_id", flat=True).first()
    if seccion.docente_id == guardado:
        return
    if guardado is not None:
        raise ValidationError({"docente": SECCION_OCUPADA})
    # La cuenta se relee: ``seccion.docente`` puede ser una copia vieja (activa, con otro rol
    # o de otra institución cuando ya no lo es en la base).
    elegible = Usuario.objects.filter(
        pk=seccion.docente_id,
        rol=Usuario.Rol.DOCENTE,
        is_active=True,
        institucion_id=seccion.anio_escolar.institucion_id,
    ).exists()
    if not elegible:
        raise ValidationError({"docente": DOCENTE_NO_ELEGIBLE})


def cargar_secciones(institucion, anio):
    """Crea el año ABIERTO y sus secciones de 1.º a 6.º, A a D, sin docentes (US-005, D2).

    Es idempotente. Devuelve ``(anio_escolar, anio_creado, secciones_creadas)``. Si el año
    ya existe CERRADO, o la institución tiene otro año ABIERTO, lanza ``ValidationError``
    y no crea nada.
    """
    with transaction.atomic():
        existente = AnioEscolar.objects.filter(institucion=institucion, anio=anio).first()
        if existente is not None and existente.estado == AnioEscolar.Estado.CERRADO:
            raise ValidationError(f"El año {anio} está cerrado: no se cargan secciones en él.")
        otro_abierto = (
            AnioEscolar.objects.filter(institucion=institucion, estado=AnioEscolar.Estado.ABIERTO)
            .exclude(anio=anio)
            .first()
        )
        if otro_abierto is not None:
            raise ValidationError(
                f"La institución ya tiene el año {otro_abierto.anio} abierto: "
                f"ciérralo antes de cargar el {anio}."
            )
        anio_escolar, anio_creado = AnioEscolar.objects.get_or_create(
            institucion=institucion, anio=anio, defaults={"estado": AnioEscolar.Estado.ABIERTO}
        )
        secciones_creadas = 0
        for grado in GRADOS:
            for nombre in NOMBRES_SECCION:
                _, creada = Seccion.objects.get_or_create(
                    anio_escolar=anio_escolar, grado=grado, nombre=nombre
                )
                secciones_creadas += creada
    return anio_escolar, anio_creado, secciones_creadas


# --- Lista de estudiantes de una sección (US-006, D2) ---

ESTUDIANTE_REPETIDO = "Este estudiante ya está en la lista"
MAX_CARACTERES_NOMBRE = 120
AYUDA_REPETIDO = (
    "Deja una sola línea. Si son personas distintas, escribe el segundo nombre completo."
)


class SeccionConEstudiantes(Exception):
    """Pegar lista solo se usa con la sección vacía."""


class ListaConRegistros(Exception):
    """Un estudiante afectado tiene registros (asistencia o notas): no se borra ninguno."""


def _clave_orden(texto):
    """Letra a letra, sin tildes y con la Ñ entre la N y la O (alfabeto español)."""
    clave = []
    for letra in texto:
        if letra == "Ñ":
            clave.append(2 * ord("N") + 1)
        else:
            clave.append(2 * ord(unicodedata.normalize("NFD", letra)[0]))
    return clave


def estudiantes_ordenados(seccion):
    """Estudiantes por apellidos y nombres, ordenados en Python (D2).

    No depende de la *collation* de PostgreSQL, que en local y en Neon puede poner "Á"
    después de "Z". Con 60 estudiantes como máximo no cuesta nada.
    """
    return sorted(
        seccion.estudiantes.all(),
        key=lambda e: (
            _clave_orden(e.apellidos),
            _clave_orden(e.nombres),
            e.apellidos,
            e.nombres,
        ),
    )


def _errores_de_filas(filas):
    """Errores de las filas bien formadas: más de 120 caracteres y repetidos (D3, 5)."""
    errores = []
    validas = []
    for linea, apellidos, nombres in filas:
        campo = (
            "apellidos"
            if len(apellidos) > MAX_CARACTERES_NOMBRE
            else "nombres"
            if len(nombres) > MAX_CARACTERES_NOMBRE
            else None
        )
        if campo is None:
            validas.append((linea, apellidos, nombres))
        else:
            errores.append(
                ErrorLista(
                    (linea,),
                    f"los {campo} tienen más de {MAX_CARACTERES_NOMBRE} caracteres",
                    f"Usa un máximo de {MAX_CARACTERES_NOMBRE} caracteres por campo, "
                    "sin datos adicionales.",
                )
            )
    por_estudiante = {}
    for linea, apellidos, nombres in validas:
        por_estudiante.setdefault((apellidos, nombres), []).append(linea)
    errores.extend(
        ErrorLista(tuple(lineas), "el mismo estudiante", AYUDA_REPETIDO)
        for lineas in por_estudiante.values()
        if len(lineas) > 1
    )
    return errores


def importar_lista(seccion, texto):
    """Importa el texto pegado a una sección vacía, todo o nada (D2).

    Devuelve ``(cantidad, errores)``: con errores no guarda nada y la cantidad es 0. Si la
    sección ya tiene estudiantes lanza ``SeccionConEstudiantes`` sin leer el texto; la
    comprobación va bajo el bloqueo de la fila de la sección, así dos pestañas que importan
    a la vez no suman dos listas. ``bulk_create`` no llama a ``save()``: las filas ya vienen
    normalizadas de ``leer_lista_pegada``.
    """
    with transaction.atomic():
        Seccion.objects.select_for_update().get(pk=seccion.pk)
        if seccion.estudiantes.exists():
            raise SeccionConEstudiantes
        filas, errores = leer_lista_pegada(texto)
        if not filas and not errores:
            return 0, [
                ErrorLista(
                    (),
                    "Pega al menos un estudiante",
                    "Copia la columna de apellidos y nombres de tu Excel y pégala aquí",
                )
            ]
        errores = sorted(
            [*errores, *_errores_de_filas(filas)],
            key=lambda error: error.lineas[0] if error.lineas else 0,
        )
        if errores:
            return 0, errores
        Estudiante.objects.bulk_create(
            Estudiante(seccion=seccion, apellidos=apellidos, nombres=nombres)
            for _, apellidos, nombres in filas
        )
    return len(filas), []


def _guardar_estudiante(estudiante, existente=False):
    """Valida (campos y ``uq_estudiante``) y guarda; un homónimo por carrera da el mismo error.

    Con ``existente`` solo actualiza: si otra petición lo quitó entretanto, el ``save()`` normal
    lo volvería a crear con la misma PK; aquí lanza ``Estudiante.DoesNotExist``.
    """
    estudiante.full_clean()
    try:
        with transaction.atomic():
            estudiante.save(force_update=existente)
    except IntegrityError:
        raise ValidationError(ESTUDIANTE_REPETIDO) from None
    except DatabaseError:
        raise Estudiante.DoesNotExist from None
    return estudiante


def agregar_estudiante(seccion, apellidos, nombres):
    """Agrega un estudiante normalizado a la sección; ``ValidationError`` si no es válido."""
    estudiante = Estudiante(
        seccion=seccion,
        apellidos=normalizar_nombre(apellidos),
        nombres=normalizar_nombre(nombres),
    )
    return _guardar_estudiante(estudiante)


def editar_estudiante(estudiante, apellidos, nombres):
    """Corrige apellidos y nombres con las reglas de ``agregar_estudiante``.

    Si el estudiante ya no existe (quitado en otra pestaña), lanza ``Estudiante.DoesNotExist``.
    """
    estudiante.apellidos = normalizar_nombre(apellidos)
    estudiante.nombres = normalizar_nombre(nombres)
    return _guardar_estudiante(estudiante, existente=True)


def quitar_estudiante(estudiante):
    """Borra al estudiante; con registros que lo referencian lanza ``ListaConRegistros``.

    La regla no consulta tablas: aparece sola cuando US-030 cree ``asistencia`` con FK
    ``RESTRICT``.
    """
    try:
        with transaction.atomic():
            estudiante.delete()
    except (RestrictedError, ProtectedError):
        raise ListaConRegistros from None


def vaciar_lista(seccion):
    """Borra a todos los estudiantes de la sección o a ninguno (``ListaConRegistros``)."""
    try:
        with transaction.atomic():
            seccion.estudiantes.all().delete()
    except (RestrictedError, ProtectedError):
        raise ListaConRegistros from None
