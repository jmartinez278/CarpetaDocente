"""Reglas de negocio del módulo institucion (documento 12: capa de servicios)."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from cuentas.models import Usuario
from institucion.models import AnioEscolar, Seccion

SECCION_OCUPADA = "La sección ya tiene un docente asignado"
SIN_SECCION = "Tu sección aparecerá cuando el administrador la asigne."
GRADOS = range(1, 7)
NOMBRES_SECCION = ("A", "B", "C", "D")
DOCENTE_NO_ELEGIBLE = "Elige una docente activa de la institución del año escolar."


def texto_seccion(seccion):
    """Texto de una sección: "2.º grado, sección A", con el ordinal º (U+00BA) (US-005, D2)."""
    return f"{seccion.grado}.º grado, sección {seccion.nombre}"


def texto_secciones_docente(usuario):
    """Línea de la portada con las secciones del docente en el año ABIERTO (US-005, D2).

    Van ordenadas por grado y nombre y unidas con " · ". Sin ninguna, avisa que aparecerá.
    """
    secciones = Seccion.objects.filter(
        docente=usuario, anio_escolar__estado=AnioEscolar.Estado.ABIERTO
    ).order_by("grado", "nombre")
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
