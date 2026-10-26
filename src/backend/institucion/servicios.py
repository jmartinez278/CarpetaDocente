"""Reglas de negocio del módulo institucion (documento 12: capa de servicios)."""

from django.core.exceptions import ValidationError
from django.db.models import Q

from cuentas.models import Usuario
from institucion.models import Seccion

SECCION_OCUPADA = "La sección ya tiene un docente asignado"
DOCENTE_NO_ELEGIBLE = "Elige una docente activa de la institución del año escolar."


def texto_seccion(seccion):
    """Texto de una sección: "2.º grado, sección A", con el ordinal º (U+00BA) (US-005, D2)."""
    return f"{seccion.grado}.º grado, sección {seccion.nombre}"


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
      Docente de la institución del año escolar.

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
    docente = seccion.docente
    if not (
        docente.is_active
        and docente.rol == Usuario.Rol.DOCENTE
        and docente.institucion_id == seccion.anio_escolar.institucion_id
    ):
        raise ValidationError({"docente": DOCENTE_NO_ELEGIBLE})
