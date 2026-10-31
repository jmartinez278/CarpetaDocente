"""Servicios del registro de actividad (design de US-008, D2 y D7).

``registrar`` es la única función que crea entradas. La llaman los servicios dentro de su
``atomic()``, la mezcla del panel y los receptores de sesión; las vistas nunca.
"""

import csv
import io
import json
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import connection, transaction
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.utils import timezone

from actividad.models import CUENTAN_KPI_01, Operacion, RegistroActividad
from cuentas.models import Usuario
from institucion.models import AnioEscolar

# La consulta, la exportación y los indicadores se leen en hora de Lima (D9, D10, D11).
LIMA = ZoneInfo("America/Lima")
FORMATO_FECHA_HORA = "%d-%m-%Y %H:%M:%S"

# Claves de detalle permitidas por operación (RN-015): ids, códigos, cantidades, fechas, estados
# y listas de nombres de campos; nunca nombres de estudiantes ni notas. Cada historia agrega las
# de su operación; una operación sin lista no admite detalle.
DETALLE_PERMITIDO: dict[Operacion, frozenset[str]] = {
    Operacion.CIERRE_SESION: frozenset({"motivo"}),
    Operacion.CUENTA_EDITADA: frozenset({"campos"}),
    Operacion.INSTITUCION_EDITADA: frozenset({"campos"}),
    Operacion.ANIO_EDITADO: frozenset({"campos"}),
    Operacion.PERIODOS_CONFIGURADOS: frozenset({"periodos"}),
    Operacion.PERIODO_EDITADO: frozenset(
        {"numero", "inicio_antes", "fin_antes", "inicio_despues", "fin_despues"}
    ),
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
    Operacion.DEMO_CARGADA: frozenset({"secciones", "estudiantes", "dias"}),
    Operacion.DEMO_QUITADA: frozenset(
        {"secciones", "cuentas", "estudiantes", "jornadas", "estados"}
    ),
    Operacion.SECCION_DESCARTADA: frozenset({"estudiantes", "jornadas", "estados"}),
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


def inicio_del_dia(dia: date) -> datetime:
    """Las 00:00 de ``dia`` en hora de Lima, para filtrar por días de Lima."""
    return datetime.combine(dia, time.min, tzinfo=LIMA)


# Columnas del CSV exportado (D10).
COLUMNAS_CSV = ["Fecha y hora", "Usuario", "Operación", "Entidad", "Identificador", "Detalle"]


def celda_segura(valor: str) -> str:
    """Pone un apóstrofo delante de un valor que una hoja de cálculo tomaría por fórmula.

    Cuenta lo que empieza con ``=``, ``+``, ``-`` o ``@``, también tras espacios o tabulaciones,
    y lo que empieza con tabulación o retorno de carro.
    """
    if valor[:1] in ("\t", "\r") or valor.lstrip(" \t\r\n")[:1] in ("=", "+", "-", "@"):
        return "'" + valor
    return valor


def exportar_csv(entradas, usuario, filtros) -> str:
    """CSV (UTF-8 con BOM) de ``entradas`` en su orden, y su REGISTRO_EXPORTADO (D10).

    La lectura y la entrada van en la misma transacción. ``filtros`` son los parámetros de la
    lista del panel (operación, usuario, fechas), sin datos personales.
    """
    salida = io.StringIO()
    salida.write("\ufeff")  # BOM: Excel muestra bien las tildes
    escritor = csv.writer(salida)
    escritor.writerow(COLUMNAS_CSV)
    with transaction.atomic():
        filas = 0
        for entrada in entradas:
            escritor.writerow(
                celda_segura(valor)
                for valor in (
                    timezone.localtime(entrada.fecha_hora, LIMA).strftime(FORMATO_FECHA_HORA),
                    entrada.usuario.username if entrada.usuario else "",
                    entrada.operacion,
                    entrada.entidad,
                    entrada.entidad_id,
                    json.dumps(entrada.detalle, ensure_ascii=False, sort_keys=True),
                )
            )
            filas += 1
        registrar(
            usuario,
            Operacion.REGISTRO_EXPORTADO,
            detalle={"filtros": dict(filtros), "filas": filas},
        )
    return salida.getvalue()


def rango_por_defecto(hoy: date) -> tuple[date, date]:
    """Del 1 de enero del año ABIERTO (el más reciente, si hay varios) a ``hoy`` (D9).

    Sin año abierto, o si el abierto aún no empieza (se abre antes de enero), el año en curso.
    """
    anio = (
        AnioEscolar.objects.filter(estado=AnioEscolar.Estado.ABIERTO)
        .order_by("-anio")
        .values_list("anio", flat=True)
        .first()
    )
    desde = date(anio, 1, 1) if anio else date(hoy.year, 1, 1)
    if desde > hoy:
        desde = date(hoy.year, 1, 1)
    return desde, hoy


def texto_activos(activos: int, participantes: int) -> str:
    """ "3 / 5 (60 %)"; sin participantes, "0 / 0 (—)"."""
    if not participantes:
        return f"{activos} / {participantes} (—)"
    return f"{activos} / {participantes} ({round(100 * activos / participantes)} %)"


def _participantes():
    """Docentes activas, no demo, con sección en un año ABIERTO, con el estado de hoy (D9)."""
    return (
        Usuario.objects.filter(
            rol=Usuario.Rol.DOCENTE,
            is_active=True,
            es_demo=False,
            secciones__anio_escolar__estado=AnioEscolar.Estado.ABIERTO,
        )
        .distinct()
        .values_list("pk", flat=True)
    )


def _por_semana(entradas, conteo):
    """``{lunes: n}`` de ``entradas`` agrupadas por semana de Lima (lunes a domingo)."""
    filas = (
        entradas.annotate(semana=TruncWeek("fecha_hora", tzinfo=LIMA))
        .values("semana")
        .annotate(n=conteo)
    )
    return {timezone.localtime(f["semana"], LIMA).date(): f["n"] for f in filas}


def indicadores_por_semana(desde: date, hasta: date) -> list[dict]:
    """Una fila por semana, del lunes de ``desde`` al domingo de ``hasta`` (D9).

    ``activos``: participantes con una operación de KPI-01 en la semana. ``jornadas``: entradas
    REGISTRO_ASISTENCIA de cuentas reales. ``sesiones`` y ``secciones_con_notas`` quedan en
    ``None`` hasta US-010 y US-020.
    """
    primer_lunes = desde - timedelta(days=desde.weekday())
    ultimo_lunes = hasta - timedelta(days=hasta.weekday())
    semana = RegistroActividad.objects.filter(
        fecha_hora__gte=inicio_del_dia(primer_lunes),
        fecha_hora__lt=inicio_del_dia(ultimo_lunes + timedelta(days=7)),
    )
    participantes = list(_participantes())
    activos = _por_semana(
        semana.filter(operacion__in=CUENTAN_KPI_01, usuario_id__in=participantes),
        Count("usuario", distinct=True),
    )
    jornadas = _por_semana(
        semana.filter(
            operacion=Operacion.REGISTRO_ASISTENCIA,
            usuario__isnull=False,
            usuario__es_demo=False,
        ),
        Count("id"),
    )

    filas = []
    lunes = primer_lunes
    while lunes <= ultimo_lunes:
        n_activos = activos.get(lunes, 0)
        filas.append(
            {
                "lunes": lunes,
                "domingo": lunes + timedelta(days=6),
                "activos": n_activos,
                "participantes": len(participantes),
                "activos_texto": texto_activos(n_activos, len(participantes)),
                "jornadas": jornadas.get(lunes, 0),
                "sesiones": None,
                "secciones_con_notas": None,
            }
        )
        lunes += timedelta(days=7)
    return filas
