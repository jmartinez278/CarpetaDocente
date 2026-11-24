"""Servicios de la dirección: periodo elegido, estado de las secciones y resumen de la I.E.

Design de US-040, D3 y D4. Solo leen. Una sola función por cifra: el mapa, el resumen, la
portada y el detalle usan estas, para que sus números no se separen (RNF-017). Las funciones
que dependen del día reciben ``hoy`` para que las pruebas lo fijen sin tocar el reloj.
"""

from dataclasses import dataclass, field

from django.db.models import Count, Q

from asistencia import servicios as asistencia
from cuentas.models import Usuario
from institucion.models import AnioEscolar, Estudiante, Seccion
from institucion.servicios import texto_seccion_corto
from notas import servicios as notas
from repositorio.models import Sesion

SIN_DOCENTE = "SIN_DOCENTE"
SIN_ESTUDIANTES = "SIN_ESTUDIANTES"
ATRASADA = "ATRASADA"
AL_DIA = "AL_DIA"

DEFINICION_AL_DIA = "Al día: sin notas que falten y sin días por completar."


# --- D4. Periodo elegido ---


def periodos_del_anio(institucion, hoy):
    """Los periodos del año ABIERTO de la institución con su estado; sin año o sin periodos,
    lista vacía."""
    anio = AnioEscolar.objects.filter(
        institucion=institucion, estado=AnioEscolar.Estado.ABIERTO
    ).first()
    if anio is None:
        return []
    return notas.periodos_del_anio_escolar(anio, hoy)


def periodo_de_la_consulta(periodos, pedido):
    """El periodo con que abren Consolidados y el detalle (D4), o ``None``.

    El pedido (``?periodo=N``) si es ANTERIOR o VIGENTE; si no, el VIGENTE; si no, el último
    ANTERIOR (entre periodos); si no, ninguno (antes del primero o sin periodos). Un futuro
    pedido abre el vigente. Es la regla de la hoja de notas sin la parte de edición.
    """
    consultables = [p for p in periodos if p.estado in (notas.ANTERIOR, notas.VIGENTE)]
    for periodo in consultables:
        if str(periodo.numero) == pedido:
            return periodo
    vigente = next((p for p in consultables if p.estado == notas.VIGENTE), None)
    if vigente is not None:
        return vigente
    return consultables[-1] if consultables else None


# --- D3. Estado de las secciones ---


@dataclass
class EstadoSeccion:
    """Una sección del año ABIERTO en un periodo, con su estado y sus cifras."""

    seccion: Seccion
    tutora: Usuario | None
    estudiantes: int
    notas_faltan: int = 0
    notas_total: int = 0
    dias_sin_completar: int = 0
    estado: str = AL_DIA

    @property
    def notas_registradas(self):
        return self.notas_total - self.notas_faltan

    @property
    def considerada(self):
        """Cuenta en «N de M»: ni «Sin docente» ni «Sin estudiantes»."""
        return self.estado in (ATRASADA, AL_DIA)


def estado_de_las_secciones(institucion, periodo, hoy):
    """Las secciones del año ABIERTO de la institución, por grado y nombre, con su estado en
    ``periodo`` (un ``Periodo``). Cuatro consultas para todas (D3).

    El estado es el primero que se cumple: «Sin docente», «Sin estudiantes» (sin activos),
    «Atrasada» (notas que faltan o días sin completar) y «Al día». Las dos primeras no suman
    notas ni días.
    """
    secciones = list(
        Seccion.objects.filter(
            anio_escolar__institucion=institucion,
            anio_escolar__estado=AnioEscolar.Estado.ABIERTO,
        )
        .select_related("docente")
        .annotate(
            activos=Count("estudiantes", filter=Q(estudiantes__estado=Estudiante.Estado.ACTIVO))
        )
        .order_by("grado", "nombre")
    )
    con_trabajo = [s for s in secciones if s.docente_id is not None and s.activos]
    faltantes = notas.faltantes_por_seccion(con_trabajo, periodo) if con_trabajo else {}
    dias = (
        asistencia.dias_sin_completar_por_seccion(con_trabajo, periodo, hoy) if con_trabajo else {}
    )
    estados = []
    for seccion in secciones:
        estado = EstadoSeccion(seccion=seccion, tutora=seccion.docente, estudiantes=seccion.activos)
        if seccion.docente_id is None:
            estado.estado = SIN_DOCENTE
        elif not seccion.activos:
            estado.estado = SIN_ESTUDIANTES
        else:
            conteo = faltantes[seccion.pk]
            estado.notas_faltan, estado.notas_total = conteo.faltan, conteo.total
            estado.dias_sin_completar = dias[seccion.pk]
            atrasada = estado.notas_faltan or estado.dias_sin_completar
            estado.estado = ATRASADA if atrasada else AL_DIA
        estados.append(estado)
    return estados


# --- D3 y D4. Resumen de la I.E. ---


@dataclass
class ResumenIE:
    """El recuadro café de Consolidados para un periodo."""

    al_dia: int
    consideradas: int
    notas_faltan: int
    dias_sin_completar: int
    porcentaje: object
    sesiones: int
    fecha_fin: object
    terminado: bool
    dias_para_el_cierre: int
    sin_docente: list[Seccion] = field(default_factory=list)
    sin_estudiantes: list[Seccion] = field(default_factory=list)

    @property
    def texto_porcentaje(self):
        return asistencia.texto_porcentaje(self.porcentaje)

    @property
    def texto_cierre(self):
        """«Faltan N días para el cierre» en el vigente; «Terminado» en uno anterior."""
        if self.terminado:
            return "Terminado"
        if self.dias_para_el_cierre == 0:
            return "Hoy es el cierre"
        if self.dias_para_el_cierre == 1:
            return "Falta 1 día para el cierre"
        return f"Faltan {self.dias_para_el_cierre} días para el cierre"

    @property
    def nota_del_pie(self):
        """Qué es «al día» y qué secciones no cuentan: «4.º C no tiene docente y 6.º D…»."""
        partes = [f"{_corto(s)} no tiene docente" for s in self.sin_docente]
        partes += [f"{_corto(s)} no tiene estudiantes" for s in self.sin_estudiantes]
        if not partes:
            return DEFINICION_AL_DIA
        lista = partes[0] if len(partes) == 1 else f"{', '.join(partes[:-1])} y {partes[-1]}"
        return f"{DEFINICION_AL_DIA} {lista}."


def _corto(seccion):
    """«4.º C» con espacio que no se parte."""
    return texto_seccion_corto(seccion).replace(" ", " ")


def sesiones_del_periodo(periodo):
    """Las sesiones propias enviadas en la I.E. del periodo, con fecha de envío (Lima) en él."""
    return Sesion.objects.filter(
        institucion__anios_escolares=periodo.anio_escolar_id,
        origen=Sesion.Origen.PROPIA,
        creado_en__date__gte=periodo.fecha_inicio,
        creado_en__date__lte=periodo.fecha_fin,
    ).count()


def resumen_de_la_ie(estados, periodo, hoy):
    """El resumen de ``estados`` (de ``estado_de_las_secciones``) en ``periodo``. Dos consultas.

    El porcentaje es el promedio de las secciones consideradas con marcas, ponderado por sus
    estudiantes activos (D5).
    """
    consideradas = [e for e in estados if e.considerada]
    totales = asistencia.totales_por_seccion([e.seccion for e in consideradas], periodo, hoy)
    porcentaje = asistencia.promedio_ponderado(
        (e.estudiantes, totales[e.seccion.pk].porcentaje) for e in consideradas
    )
    return ResumenIE(
        al_dia=sum(e.estado == AL_DIA for e in consideradas),
        consideradas=len(consideradas),
        notas_faltan=sum(e.notas_faltan for e in consideradas),
        dias_sin_completar=sum(e.dias_sin_completar for e in consideradas),
        porcentaje=porcentaje,
        sesiones=sesiones_del_periodo(periodo),
        fecha_fin=periodo.fecha_fin,
        terminado=periodo.fecha_fin < hoy,
        dias_para_el_cierre=max((periodo.fecha_fin - hoy).days, 0),
        sin_docente=[e.seccion for e in estados if e.estado == SIN_DOCENTE],
        sin_estudiantes=[e.seccion for e in estados if e.estado == SIN_ESTUDIANTES],
    )
