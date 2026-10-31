"""Servicios de notas: toda regla y toda escritura de las marcas (design de US-029, D3 a D7).

Las vistas solo leen la petición y llaman aquí. Las funciones que dependen del día reciben
``hoy`` (por defecto, la fecha de Lima) para que las pruebas lo fijen sin tocar el reloj.

``puede_marcar``, ``tiene_notas`` y ``competencias_obligatorias`` son los únicos puntos que
cambian US-020 y la historia de docentes de curso.
"""

from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, Prefetch
from django.utils import timezone

from actividad.models import Operacion
from actividad.servicios import registrar
from catalogo.models import Area, Competencia, InstitucionArea
from cuentas.models import Usuario
from institucion.models import AnioEscolar, Institucion, Periodo, Seccion
from institucion.servicios import periodo_vigente
from notas.models import CompetenciaPeriodo

CONJUNTO_NO_VALIDO = "Las competencias enviadas no son válidas. Recarga la página."
SIN_MARCAS = "Marca al menos una competencia para guardar."
MENSAJE_CON_NOTAS = "La competencia tiene notas registradas en este periodo"
PERIODO_NO_MARCABLE = "Este periodo no se puede marcar."

VIGENTE = "VIGENTE"
ANTERIOR = "ANTERIOR"
FUTURO = "FUTURO"


class PeriodoNoMarcable(Exception):
    """El año está CERRADO o el periodo aún no empieza: no se guarda nada."""

    def __init__(self, mensaje=PERIODO_NO_MARCABLE):
        super().__init__(mensaje)


class CompetenciaConNotas(Exception):
    """El guardado quita competencias con notas en el periodo: no se guarda nada (D6)."""

    def __init__(self, competencias):
        super().__init__(MENSAJE_CON_NOTAS)
        self.competencias = competencias


# --- D3. Lo que ve y marca la tutora ---


@dataclass
class AreaDeLaSeccion:
    """Un área que la institución trabaja, con sus competencias activas en orden."""

    area: Area
    competencias: list[Competencia]
    a_cargo: bool
    marcable: bool


def puede_marcar(usuario, seccion, area_institucion):
    """Si ``usuario`` marca las competencias de ``area_institucion`` en ``seccion`` (decisión 13).

    Cuenta con rol Docente que es la docente de la sección, en un área de la institución de la
    sección que se trabaja y no está a cargo del docente de curso. No mira el año ni el periodo.
    """
    return (
        getattr(usuario, "rol", None) == Usuario.Rol.DOCENTE
        and seccion.docente_id is not None
        and seccion.docente_id == usuario.pk
        and area_institucion.institucion_id == seccion.anio_escolar.institucion_id
        and area_institucion.se_trabaja
        and not area_institucion.a_cargo_docente_curso
    )


def areas_de_la_seccion(usuario, seccion):
    """Las áreas que trabaja la institución de la sección, en orden SIAGIE (RN-007, RN-008).

    Cada una con sus competencias activas por ``orden``, si está a cargo del docente de curso y
    si ``usuario`` la marca. Dos consultas.
    """
    filas = (
        InstitucionArea.objects.filter(
            institucion_id=seccion.anio_escolar.institucion_id, se_trabaja=True
        )
        .select_related("area")
        .prefetch_related(
            Prefetch(
                "area__competencias",
                queryset=Competencia.objects.filter(activa=True).order_by("orden", "pk"),
                to_attr="activas",
            )
        )
        .order_by("area__orden", "area__pk")
    )
    return [
        AreaDeLaSeccion(
            area=fila.area,
            competencias=fila.area.activas,
            a_cargo=fila.a_cargo_docente_curso,
            marcable=puede_marcar(usuario, seccion, fila),
        )
        for fila in filas
    ]


def universo_de_las_areas(areas):
    """Los id de las competencias activas de las áreas marcables, sin volver a consultar.

    ``areas`` es lo que devuelve ``areas_de_la_seccion``; es la única regla del universo.
    """
    return {competencia.pk for area in areas if area.marcable for competencia in area.competencias}


def universo(usuario, seccion):
    """Los id de las competencias activas que ``usuario`` marca en ``seccion``.

    Es el conjunto que el guardado valida, compara y borra (D5).
    """
    return universo_de_las_areas(areas_de_la_seccion(usuario, seccion))


# --- D4. Periodos ---


@dataclass
class PeriodoDeLaSeccion:
    """Un periodo del año de la sección, con su estado respecto de ``hoy``."""

    periodo: Periodo
    nombre: str
    nombre_largo: str
    estado: str
    editable: bool

    @property
    def numero(self):
        return self.periodo.numero

    @property
    def fecha_inicio(self):
        return self.periodo.fecha_inicio

    @property
    def fecha_fin(self):
        return self.periodo.fecha_fin


def periodos_de_la_seccion(seccion, hoy=None):
    """Los periodos del año de la sección por número, con estado y si se marcan (D4).

    VIGENTE es el de ``periodo_vigente``; ANTERIOR, el que terminó; FUTURO, el que aún no
    empieza. Se marca el que ya empezó, solo con el año ABIERTO. Sin periodos, lista vacía.
    """
    hoy = hoy or timezone.localdate()
    anio = seccion.anio_escolar
    periodos = list(Periodo.objects.filter(anio_escolar_id=anio.pk).order_by("numero"))
    if not periodos:
        return []
    vigente = periodo_vigente(anio, hoy)
    trimestres = (
        anio.institucion.organizacion_periodos == Institucion.OrganizacionPeriodos.TRIMESTRE
    )
    letra, palabra = ("T", "Trimestre") if trimestres else ("B", "Bimestre")
    abierto = anio.estado == AnioEscolar.Estado.ABIERTO
    resultado = []
    for periodo in periodos:
        if vigente is not None and periodo.pk == vigente.pk:
            estado = VIGENTE
        elif periodo.fecha_fin < hoy:
            estado = ANTERIOR
        else:
            estado = FUTURO
        resultado.append(
            PeriodoDeLaSeccion(
                periodo=periodo,
                nombre=f"{letra}{periodo.numero}",
                nombre_largo=f"{palabra} {periodo.numero}",
                estado=estado,
                editable=abierto and periodo.fecha_inicio <= hoy,
            )
        )
    return resultado


# --- D6 y D7. Notas y obligatorias ---


def tiene_notas(seccion, periodo, competencia):
    """Si la competencia tiene notas de la sección en el periodo (decisión 7).

    Devuelve ``False`` hasta que US-020 cree ``calificacion``; es el único lugar que lo sabe.
    """
    return False


def competencias_obligatorias(usuario, seccion, periodo, universo_actual=None):
    """En el último periodo del año ABIERTO, las del universo sin marca en los anteriores (D7).

    En cualquier otro periodo, o con el año CERRADO, ninguna. ``universo_actual`` evita volver a
    calcular el universo cuando quien llama ya lo tiene.
    """
    if seccion.anio_escolar.estado != AnioEscolar.Estado.ABIERTO:
        return set()
    ultimo = Periodo.objects.filter(anio_escolar_id=periodo.anio_escolar_id).aggregate(
        ultimo=Max("numero")
    )["ultimo"]
    if periodo.numero != ultimo:
        return set()
    if universo_actual is None:
        universo_actual = universo(usuario, seccion)
    marcadas_antes = CompetenciaPeriodo.objects.filter(
        seccion=seccion,
        periodo__anio_escolar_id=periodo.anio_escolar_id,
        periodo__numero__lt=periodo.numero,
    ).values_list("competencia_id", flat=True)
    return set(universo_actual) - set(marcadas_antes)


# --- D5. Guardado ---


@dataclass
class CambiosMarcas:
    """Lo que cambió un guardado: listas ordenadas de id de competencia."""

    agregadas: list[int] = field(default_factory=list)
    quitadas: list[int] = field(default_factory=list)


def estado_inicial(permitido, guardadas, obligatorias):
    """Las marcas con que abre un periodo: lo guardado, o todo ``permitido`` si no tiene marcas.

    ``guardadas`` es ``None`` (sin marcas dentro del universo) o la lista de id guardados; a eso se
    suman las ``obligatorias`` (spec «Estado inicial del periodo»; no cuentan como cambio).
    """
    base = set(permitido) if guardadas is None else set(guardadas)
    return base | set(obligatorias)


def marcas_por_periodo(seccion, permitido):
    """Por id de periodo, los id marcados en la sección dentro de ``permitido``, ordenados.

    Un periodo sin marcas dentro de ``permitido`` no aparece: la pantalla lo abre con todo
    marcado (spec «Estado inicial del periodo»). Una consulta.
    """
    marcas = {}
    filas = (
        CompetenciaPeriodo.objects.filter(seccion=seccion, competencia_id__in=permitido)
        .order_by("periodo_id", "competencia_id")
        .values_list("periodo_id", "competencia_id")
    )
    for periodo_id, competencia_id in filas:
        marcas.setdefault(periodo_id, []).append(competencia_id)
    return marcas


def _marcas_existentes(seccion, periodo, permitido):
    """Los id marcados en el periodo dentro de ``permitido``; las demás marcas no se leen."""
    return set(
        CompetenciaPeriodo.objects.filter(
            seccion=seccion, periodo=periodo, competencia_id__in=permitido
        ).values_list("competencia_id", flat=True)
    )


def guardar_marcas(usuario, seccion, numero, ids, hoy=None, *, visto):
    """Guarda el conjunto completo de marcas del periodo ``numero``, todo o nada (D5).

    Bloquea la sección: dos guardados del mismo periodo van en fila y el segundo compara con lo
    que dejó el primero. Compara, crea y borra solo dentro del ``universo`` de ``usuario``; las
    obligatorias del último periodo se agregan aunque no vengan. Deja COMPETENCIAS_MARCADAS si
    algo cambió (D10). Devuelve ``CambiosMarcas``.

    ``visto`` es el universo que mostró la pantalla. Si ya no es el de ahora (el Administrador
    activó o desactivó una competencia con la pantalla abierta), no se guarda nada: el envío
    omitiría una marca que la tutora no vio y el guardado la borraría (escenario «Catálogo
    cambiado al guardar»).

    Lanza ``PeriodoNoMarcable`` (año CERRADO o periodo que no empezó), ``Periodo.DoesNotExist``
    (no hay ese número en el año de la sección), ``ValidationError`` con ``CONJUNTO_NO_VALIDO``
    o ``SIN_MARCAS`` y ``CompetenciaConNotas``.
    """
    hoy = hoy or timezone.localdate()
    ids = set(ids)
    with transaction.atomic():
        seccion = (
            Seccion.objects.select_for_update(of=("self",))
            .select_related("anio_escolar__institucion")
            .get(pk=seccion.pk)
        )
        if seccion.anio_escolar.estado != AnioEscolar.Estado.ABIERTO:
            raise PeriodoNoMarcable
        periodo = Periodo.objects.get(anio_escolar_id=seccion.anio_escolar_id, numero=numero)
        if periodo.fecha_inicio > hoy:
            raise PeriodoNoMarcable
        permitido = universo(usuario, seccion)
        if set(visto) != permitido or not ids <= permitido:
            raise ValidationError(CONJUNTO_NO_VALIDO)
        nuevo = ids | competencias_obligatorias(usuario, seccion, periodo, permitido)
        if not nuevo:
            raise ValidationError(SIN_MARCAS)
        existentes = _marcas_existentes(seccion, periodo, permitido)
        quitadas = sorted(existentes - nuevo)
        con_notas = [c for c in quitadas if tiene_notas(seccion, periodo, c)]
        if con_notas:
            raise CompetenciaConNotas(con_notas)
        agregadas = sorted(nuevo - existentes)
        CompetenciaPeriodo.objects.bulk_create(
            CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=competencia)
            for competencia in agregadas
        )
        if quitadas:
            CompetenciaPeriodo.objects.filter(
                seccion=seccion, periodo=periodo, competencia_id__in=quitadas
            ).delete()
        if agregadas or quitadas:
            registrar(
                usuario,
                Operacion.COMPETENCIAS_MARCADAS,
                entidad="seccion",
                entidad_id=seccion,
                detalle={"periodo": periodo.numero, "agregadas": agregadas, "quitadas": quitadas},
            )
    return CambiosMarcas(agregadas, quitadas)


# --- D11. Demostración ---


def marcar_todo_sin_registro(seccion, periodos):
    """Marca el universo de la docente de la sección en cada periodo que no tiene marcas (D11).

    Sin entrada propia: la carga de la demostración deja su DEMO_CARGADA, como
    ``importar_lista_sin_registro``. Va dentro de la transacción de quien la llama. Devuelve
    cuántas marcas creó.
    """
    periodos = list(periodos)
    if not periodos:
        return 0
    todas = sorted(universo(seccion.docente, seccion))
    con_marcas = set(
        CompetenciaPeriodo.objects.filter(seccion=seccion, periodo__in=periodos).values_list(
            "periodo_id", flat=True
        )
    )
    nuevas = CompetenciaPeriodo.objects.bulk_create(
        CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=competencia)
        for periodo in periodos
        if periodo.pk not in con_marcas
        for competencia in todas
    )
    return len(nuevas)
