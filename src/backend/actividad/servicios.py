"""Servicios del registro de actividad (design de US-008, D2 y D7).

``registrar`` es la única función que crea entradas. La llaman los servicios dentro de su
``atomic()``, la mezcla del panel y los receptores de sesión; las vistas nunca.
"""

from django.db import connection

from actividad.models import Operacion, RegistroActividad

# Claves de detalle permitidas por operación (RN-015): ids, códigos, cantidades, fechas, estados
# y listas de nombres de campos; nunca nombres de estudiantes ni notas. Cada historia agrega las
# de su operación; una operación sin lista no admite detalle.
DETALLE_PERMITIDO: dict[Operacion, frozenset[str]] = {
    Operacion.CIERRE_SESION: frozenset({"motivo"}),
    Operacion.CUENTA_EDITADA: frozenset({"campos"}),
    Operacion.INSTITUCION_EDITADA: frozenset({"campos"}),
    Operacion.ANIO_EDITADO: frozenset({"campos"}),
    Operacion.SECCION_EDITADA: frozenset({"campos"}),
    Operacion.SECCION_ASIGNADA: frozenset({"docente_anterior", "docente_nuevo"}),
    Operacion.SECCION_LIBERADA: frozenset({"docente_anterior", "docente_nuevo"}),
    Operacion.ESTUDIANTES_IMPORTADOS: frozenset({"cantidad"}),
    Operacion.ESTUDIANTE_EDITADO: frozenset({"campos"}),
    Operacion.LISTA_VACIADA: frozenset({"cantidad"}),
    Operacion.REGISTRO_ASISTENCIA: frozenset({"seccion", "fecha"}),
    Operacion.ASISTENCIA_CAMBIADA: frozenset(
        {"estudiante", "anterior", "nuevo", "nota_cambiada", "origen"}
    ),
    Operacion.CATALOGO_EDITADO: frozenset({"campos"}),
    Operacion.REGISTRO_EXPORTADO: frozenset({"filtros", "filas"}),
}


def registrar(usuario, operacion, entidad="", entidad_id="", detalle=None):
    """Guarda una entrada de actividad en la transacción de la operación que registra.

    ``usuario`` vacío (``None`` o sin autenticar) es un comando de consola. ``entidad_id`` puede
    ser el objeto afectado o su id; se guarda como texto.

    Lanza ``RuntimeError`` si no hay una transacción abierta (la entrada y la operación van
    juntas o no van) y ``ValueError`` si la operación no es del catálogo o el detalle trae
    claves no permitidas. En ambos casos no guarda nada.
    """
    if not connection.in_atomic_block:
        raise RuntimeError(
            "registrar debe llamarse dentro de una transacción (transaction.atomic)."
        )

    if operacion not in Operacion.values:
        raise ValueError(f"La operación {operacion!r} no está en el catálogo.")
    operacion = Operacion(operacion)

    detalle = dict(detalle or {})
    sobran = set(detalle) - DETALLE_PERMITIDO.get(operacion, frozenset())
    if sobran:
        raise ValueError(
            f"El detalle de {operacion} no admite las claves {sorted(sobran)} (RN-015)."
        )

    if not getattr(usuario, "is_authenticated", False):
        usuario = None
    entidad_id = getattr(entidad_id, "pk", entidad_id)

    return RegistroActividad.objects.create(
        usuario=usuario,
        operacion=operacion,
        entidad=entidad,
        entidad_id="" if entidad_id is None else str(entidad_id),
        detalle=detalle,
    )
