"""Servicios de asistencia: toda regla y toda escritura de la jornada (design de US-030, D2).

Las vistas solo leen la petición y llaman aquí. Cada función recibe ``hoy`` (por defecto, la
fecha de Lima) para que las pruebas fijen el día sin tocar el reloj.
"""

from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from asistencia.models import Asistencia, Jornada
from institucion.models import Estudiante
from institucion.servicios import estudiantes_ordenados

MAX_CARACTERES_NOTA = 100
ESTADOS = [estado for estado, _ in Asistencia.Estado.choices]

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


class FechaNoValida(Exception):
    """La fecha no es hoy o no es día de clases: no se guarda nada."""


@dataclass
class Fila:
    """Un estudiante activo en la pantalla: ``estado`` y ``nota`` son None/'' si está Sin marcar."""

    numero: int
    estudiante: Estudiante
    estado: str | None
    nota: str


@dataclass
class ListaDeHoy:
    """Lo que la pantalla necesita de la jornada de hoy, sin haberla creado."""

    jornada: Jornada | None
    filas: list[Fila]
    no_activos: list[Estudiante]
    totales: dict[str, int] = field(default_factory=dict)

    @property
    def total(self):
        return len(self.filas)

    @property
    def marcados(self):
        return sum(1 for fila in self.filas if fila.estado is not None)

    @property
    def sin_marcar(self):
        return self.total - self.marcados

    @property
    def completa(self):
        """Hay estudiantes activos y todos tienen estado (se calcula, no se guarda: doc 11)."""
        return self.total > 0 and self.sin_marcar == 0


def es_dia_de_clases(fecha):
    """De lunes a viernes; los feriados no se distinguen."""
    return fecha.weekday() < 5


def texto_fecha(fecha):
    """ "Miércoles 28 de octubre", sin depender del idioma del servidor."""
    return f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]}"


def saludo(hora):
    """Buenos días hasta las 11:59, buenas tardes de 12:00 a 18:59 y buenas noches el resto."""
    if hora < 12:
        return "Buenos días"
    if hora < 19:
        return "Buenas tardes"
    return "Buenas noches"


def _validar_fecha(fecha, hoy):
    if fecha != hoy or not es_dia_de_clases(fecha):
        raise FechaNoValida


def _activos(seccion):
    return seccion.estudiantes.filter(estado=Estudiante.Estado.ACTIVO)


def lista_de_hoy(seccion, hoy=None):
    """Activos ordenados y numerados, no activos aparte, avance y totales; no crea la jornada."""
    hoy = hoy or timezone.localdate()
    jornada = Jornada.objects.filter(seccion=seccion, fecha=hoy).first()
    asistencias = {}
    if jornada:
        asistencias = {a.estudiante_id: a for a in jornada.asistencias.all()}

    filas = []
    no_activos = []
    for estudiante in estudiantes_ordenados(seccion):
        if estudiante.estado != Estudiante.Estado.ACTIVO:
            no_activos.append(estudiante)
            continue
        asistencia = asistencias.get(estudiante.pk)
        filas.append(
            Fila(
                numero=len(filas) + 1,
                estudiante=estudiante,
                estado=asistencia.estado if asistencia else None,
                nota=asistencia.nota_justificacion if asistencia else "",
            )
        )

    totales = dict.fromkeys(ESTADOS, 0)
    for fila in filas:
        if fila.estado is not None:
            totales[fila.estado] += 1
    return ListaDeHoy(jornada=jornada, filas=filas, no_activos=no_activos, totales=totales)


def pendiente_hoy(seccion, hoy=None):
    """Para la píldora de la portada: día de clases, con activos y la jornada sin completar."""
    hoy = hoy or timezone.localdate()
    if not es_dia_de_clases(hoy):
        return False
    return not _completa_o_vacia(seccion, hoy)


def _completa_o_vacia(seccion, hoy):
    activos = _activos(seccion).count()
    if activos == 0:
        return True
    marcados = Asistencia.objects.filter(
        jornada__seccion=seccion,
        jornada__fecha=hoy,
        estudiante__estado=Estudiante.Estado.ACTIVO,
    ).count()
    return marcados >= activos


def marcar(seccion, estudiante_id, fecha, estado, nota, usuario, hoy=None):
    """Guarda el estado de destino de un estudiante en la jornada de hoy (idempotente, D3).

    La jornada nace con el primer toque. ``FechaNoValida`` si no es hoy o es fin de semana,
    ``ValidationError`` si el estado o la nota no valen, ``Estudiante.DoesNotExist`` si no es
    un estudiante activo de la sección. Con cualquier error no se crea nada.
    """
    hoy = hoy or timezone.localdate()
    _validar_fecha(fecha, hoy)
    if estado not in ESTADOS:
        raise ValidationError("Estado de asistencia no válido")
    nota = nota or ""
    if len(nota) > MAX_CARACTERES_NOTA:
        raise ValidationError(f"La nota admite hasta {MAX_CARACTERES_NOTA} caracteres")
    if estado != Asistencia.Estado.JUSTIFICADO:
        nota = ""

    with transaction.atomic():
        estudiante = _activos(seccion).get(pk=estudiante_id)
        jornada = _jornada(seccion, fecha, usuario)
        # Un solo INSERT ... ON CONFLICT DO UPDATE: dos peticiones iguales no chocan (D2).
        Asistencia.objects.bulk_create(
            [
                Asistencia(
                    jornada=jornada,
                    estudiante=estudiante,
                    estado=estado,
                    nota_justificacion=nota,
                )
            ],
            update_conflicts=True,
            unique_fields=["jornada", "estudiante"],
            update_fields=["estado", "nota_justificacion", "actualizado_en"],
        )


def marcar_restantes(seccion, estudiante_ids, fecha, usuario, hoy=None):
    """Pone Asistió a los que aún no tienen estado hoy; nunca pisa uno ya puesto (decisión 3).

    Un id que no es un estudiante activo de la sección hace fallar todo el lote
    (``Estudiante.DoesNotExist``) sin guardar ninguno.
    """
    hoy = hoy or timezone.localdate()
    _validar_fecha(fecha, hoy)
    ids = set(estudiante_ids)
    if not ids:
        return

    with transaction.atomic():
        estudiantes = list(_activos(seccion).filter(pk__in=ids))
        if len(estudiantes) != len(ids):
            raise Estudiante.DoesNotExist
        jornada = _jornada(seccion, fecha, usuario)
        Asistencia.objects.bulk_create(
            [
                Asistencia(jornada=jornada, estudiante=estudiante, estado=Asistencia.Estado.ASISTIO)
                for estudiante in estudiantes
            ],
            ignore_conflicts=True,
        )


def _jornada(seccion, fecha, usuario):
    """La jornada única de la sección y fecha; si dos peticiones chocan, Django relee."""
    jornada, _ = Jornada.objects.get_or_create(
        seccion=seccion, fecha=fecha, defaults={"registrado_por": usuario}
    )
    return jornada
