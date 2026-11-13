"""Servicios de notas: toda regla y toda escritura de las marcas y las notas.

Marcas: design de US-029, D3 a D7. Hoja de notas: design de US-020, D2 a D7 y D14. Las vistas
solo leen la petición y llaman aquí. Las funciones que dependen del día reciben ``hoy`` (por
defecto, la fecha de Lima) para que las pruebas lo fijen sin tocar el reloj.

``puede_marcar`` es el único punto que cambia la historia de docentes de curso.
"""

from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, F, Max, OuterRef, Prefetch
from django.utils import timezone

from actividad.models import Operacion
from actividad.servicios import registrar
from catalogo.models import Area, Competencia, InstitucionArea
from cuentas.models import Usuario
from institucion.models import AnioEscolar, Estudiante, Institucion, Periodo, Seccion
from institucion.servicios import estudiantes_ordenados, periodo_vigente
from notas.models import (
    CONCLUSION_MAXIMA,
    CONCLUSION_MINIMA,
    Calificacion,
    CompetenciaPeriodo,
)

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

NUMEROS_ROMANOS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


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
    def romano(self):
        """El número en romanos («IV»), para las pantallas del rebrand."""
        return NUMEROS_ROMANOS[self.periodo.numero]

    @property
    def nombre_romano(self):
        """«IV bimestre» o «III trimestre» (la palabra sale de ``nombre_largo``)."""
        return f"{self.romano} {self.nombre_largo.split()[0].lower()}"

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


def competencias_con_notas(seccion, periodo):
    """Los id de las competencias con alguna nota de la sección en el periodo (US-020, D14).

    Una consulta; quien revisa varias competencias del mismo periodo la llama una vez.
    """
    return set(
        Calificacion.objects.filter(periodo=periodo, estudiante__seccion=seccion)
        .values_list("competencia_id", flat=True)
        .distinct()
    )


def tiene_notas(seccion, periodo, competencia):
    """Si la competencia tiene notas de la sección en el periodo (decisión 7)."""
    return getattr(competencia, "pk", competencia) in competencias_con_notas(seccion, periodo)


def competencias_obligatorias(usuario, seccion, periodo, universo_actual=None):
    """En el último periodo del año ABIERTO, las del universo sin notas en el año (D7; D14).

    Sin notas de la sección en ningún periodo del año: una marcada antes sin notas sigue siendo
    obligatoria. En cualquier otro periodo, o con el año CERRADO, ninguna. ``universo_actual``
    evita volver a calcular el universo cuando quien llama ya lo tiene.
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
    con_notas = Calificacion.objects.filter(
        estudiante__seccion=seccion, periodo__anio_escolar_id=periodo.anio_escolar_id
    ).values_list("competencia_id", flat=True)
    return set(universo_actual) - set(con_notas)


# --- US-020, D2. La hoja de notas ---


@dataclass
class Columna:
    """Una competencia marcada en el periodo, con su número del catálogo (C1, C3…)."""

    competencia: Competencia
    numero: int

    @property
    def etiqueta(self):
        return f"C{self.numero}"


@dataclass
class HojaDelArea:
    """La hoja de un área en un periodo (D2).

    ``total`` son las competencias activas del área («3 de 4 competencias marcadas»).
    ``notas`` va por ``(estudiante_id, competencia_id)`` con ``(nivel, conclusión)``. Las áreas
    a cargo del docente de curso y las marcables sin columnas van sin filas ni notas.
    """

    area: Area
    a_cargo: bool
    marcable: bool
    total: int
    columnas: list[Columna] = field(default_factory=list)
    filas: list[Estudiante] = field(default_factory=list)
    solo_lectura: list[Estudiante] = field(default_factory=list)
    notas: dict[tuple[int, int], tuple[str, str]] = field(default_factory=dict)

    @property
    def faltantes(self):
        """Celdas sin nota de las filas activas en las columnas: la regla de ``notas_faltantes``
        (D4) sobre lo ya leído, sin otra consulta. Sin columnas (docente de curso), cero."""
        return sum(
            (fila.pk, columna.competencia.pk) not in self.notas
            for fila in self.filas
            for columna in self.columnas
        )


def _columnas(area, marcadas):
    """Las competencias activas de ``area`` que están en ``marcadas``, con su número."""
    return [
        Columna(competencia=competencia, numero=numero)
        for numero, competencia in enumerate(area.competencias, start=1)
        if competencia.pk in marcadas
    ]


def hoja_de_notas(usuario, seccion, periodo, areas=None):
    """Las hojas de las áreas de la sección en ``periodo``, en orden SIAGIE (D2).

    Cinco consultas (tres si ``areas`` ya viene de ``areas_de_la_seccion``): las áreas, las
    marcas del periodo, los estudiantes y las notas del periodo. Ninguna por área ni por celda.
    """
    if areas is None:
        areas = areas_de_la_seccion(usuario, seccion)
    marcadas = set(
        CompetenciaPeriodo.objects.filter(seccion=seccion, periodo=periodo).values_list(
            "competencia_id", flat=True
        )
    )
    estudiantes = estudiantes_ordenados(seccion)
    notas = {
        (estudiante_id, competencia_id): (nivel, conclusion)
        for estudiante_id, competencia_id, nivel, conclusion in Calificacion.objects.filter(
            periodo=periodo, estudiante__seccion=seccion
        ).values_list("estudiante_id", "competencia_id", "nivel", "conclusion_descriptiva")
    }
    activos = [e for e in estudiantes if e.estado == Estudiante.Estado.ACTIVO]
    otros = [e for e in estudiantes if e.estado != Estudiante.Estado.ACTIVO]
    hojas = []
    for area in areas:
        hoja = HojaDelArea(
            area=area.area,
            a_cargo=area.a_cargo,
            marcable=area.marcable,
            total=len(area.competencias),
        )
        columnas = _columnas(area, marcadas) if area.marcable else []
        if columnas:
            ids = {columna.competencia.pk for columna in columnas}
            hoja.columnas = columnas
            hoja.filas = activos
            hoja.notas = {clave: nota for clave, nota in notas.items() if clave[1] in ids}
            con_notas = {estudiante_id for estudiante_id, _ in hoja.notas}
            hoja.solo_lectura = [e for e in otros if e.pk in con_notas]
            visibles = {e.pk for e in activos} | con_notas
            hoja.notas = {clave: nota for clave, nota in hoja.notas.items() if clave[0] in visibles}
        hojas.append(hoja)
    return hojas


# --- US-020, D3. Periodo de la hoja ---


def periodo_de_la_hoja(periodos, pedido):
    """El periodo con que abre la hoja (D3), o ``None``.

    ``periodos`` es lo que da ``periodos_de_la_seccion``; ``pedido``, el ``?periodo=N``. El
    pedido si se edita; si no, el VIGENTE; si no, el ANTERIOR editable de número mayor; si no,
    ninguno (sin periodos o antes del primero).
    """
    for periodo in periodos:
        if str(periodo.numero) == pedido and periodo.editable:
            return periodo
    vigente = next((p for p in periodos if p.estado == VIGENTE), None)
    if vigente is not None:
        return vigente
    anteriores = [p for p in periodos if p.estado == ANTERIOR and p.editable]
    return anteriores[-1] if anteriores else None


# --- US-022, D4. Notas faltantes ---


def notas_faltantes(usuario, seccion, periodo, area_institucion):
    """Los pares ``(estudiante_id, competencia_id)`` sin nota del área en el periodo (D4).

    Estudiantes activos de la sección por competencias activas del área marcadas en el periodo,
    menos los que ya tienen nota. Sin nada si ``usuario`` no marca el área (docente de curso).
    Una consulta; ``area_institucion`` es la fila ``InstitucionArea`` ya leída.
    """
    if not puede_marcar(usuario, seccion, area_institucion):
        return []
    # Las anotaciones comparten un solo JOIN a los estudiantes; filtrar por la relación en otra
    # llamada abriría otro y multiplicaría las filas.
    filas = (
        CompetenciaPeriodo.objects.filter(
            seccion=seccion,
            periodo=periodo,
            competencia__area_id=area_institucion.area_id,
            competencia__activa=True,
        )
        .annotate(
            estudiante_id=F("seccion__estudiantes__id"),
            estado_estudiante=F("seccion__estudiantes__estado"),
        )
        .filter(estado_estudiante=Estudiante.Estado.ACTIVO)
        .filter(
            ~Exists(
                Calificacion.objects.filter(
                    estudiante_id=OuterRef("estudiante_id"),
                    competencia_id=OuterRef("competencia_id"),
                    periodo_id=OuterRef("periodo_id"),
                )
            )
        )
        .order_by("estudiante_id", "competencia__orden")
        .values_list("estudiante_id", "competencia_id")
    )
    return list(filas)


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
        con_notas = competencias_con_notas(seccion, periodo) if quitadas else set()
        con_notas = [c for c in quitadas if c in con_notas]
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


# --- US-020, D5 a D7. Guardado de la hoja ---

PERIODO_NO_EDITABLE = "Este periodo no se puede editar."
HOJA_CAMBIADA = "La hoja cambió desde que la abriste. Recarga la página."
VALOR_NO_VALIDO = "Valor no válido. Use un nivel de la escala de calificación"
FALTA_CONCLUSION = "Faltan conclusiones en B y C. Escríbelas con 10 a 500 caracteres."
NOTAS_CAMBIADAS = (
    "Algunas notas cambiaron en otro dispositivo. Revisa las celdas marcadas y vuelve a guardar."
)

NIVELES = frozenset(Calificacion.Nivel.values)
CON_CONCLUSION = frozenset({Calificacion.Nivel.B, Calificacion.Nivel.C})


class PeriodoNoEditable(Exception):
    """El año está CERRADO o el periodo aún no empieza: no se guarda nada."""

    def __init__(self):
        super().__init__(PERIODO_NO_EDITABLE)


class HojaCambiada(Exception):
    """Una celda no es de la hoja (o el envío está mal formado): no se guarda nada (D5, 2)."""

    def __init__(self):
        super().__init__(HOJA_CAMBIADA)


class HojaConErrores(Exception):
    """Celdas fuera de la escala o sin conclusión válida: no se guarda nada (D5, 3 y 4).

    Ambas listas son pares ``(estudiante_id, competencia_id)`` en el orden del envío. El
    mensaje es el de la escala si hay alguna no válida; si no, el de la conclusión.
    """

    def __init__(self, no_validas, sin_conclusion):
        super().__init__(VALOR_NO_VALIDO if no_validas else FALTA_CONCLUSION)
        self.no_validas = no_validas
        self.sin_conclusion = sin_conclusion


class NotasCambiadas(Exception):
    """Notas cambiadas desde otro dispositivo desde que la docente las vio (D7).

    ``cambiadas`` trae, por celda, la nota de ahora (``nivel`` ``None`` si no hay).
    """

    def __init__(self, cambiadas):
        super().__init__(NOTAS_CAMBIADAS)
        self.cambiadas = cambiadas


@dataclass
class ResultadoHoja:
    """Lo que hizo un guardado: cuántas creó, qué pares cambió y cuántas faltan en el área."""

    creadas: int
    cambiadas: list[tuple[int, int]]
    faltantes: int


def _es_id(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _nota_de(valor):
    """``(nivel, conclusión)`` de una ``base`` del envío, o ``None``; si no es válida, falla."""
    if valor is None:
        return None
    if (
        not isinstance(valor, dict)
        or not isinstance(valor.get("nivel"), str)
        or not isinstance(valor.get("conclusion"), str)
    ):
        raise HojaCambiada
    return valor["nivel"], valor["conclusion"]


def _leer_celdas(celdas):
    """Las celdas del envío como tuplas, o ``HojaCambiada`` si la estructura no es la esperada."""
    if not isinstance(celdas, list):
        raise HojaCambiada
    leidas = []
    for celda in celdas:
        if (
            not isinstance(celda, dict)
            or not _es_id(celda.get("estudiante"))
            or not _es_id(celda.get("competencia"))
            or not isinstance(celda.get("nivel"), str)
            or not isinstance(celda.get("conclusion"), str)
            or "base" not in celda
        ):
            raise HojaCambiada
        leidas.append(
            (
                (celda["estudiante"], celda["competencia"]),
                celda["nivel"],
                celda["conclusion"],
                _nota_de(celda["base"]),
            )
        )
    return leidas


def _notas_actuales(periodo, claves):
    """Las notas de ``claves`` en el periodo, por par (estudiante, competencia); una consulta."""
    estudiantes = {estudiante for estudiante, _ in claves}
    competencias = {competencia for _, competencia in claves}
    filas = Calificacion.objects.filter(
        periodo=periodo, estudiante_id__in=estudiantes, competencia_id__in=competencias
    )
    return {
        (nota.estudiante_id, nota.competencia_id): nota
        for nota in filas
        if (nota.estudiante_id, nota.competencia_id) in claves
    }


def guardar_hoja(usuario, seccion, numero, codigo_area, celdas, hoy=None):
    """Guarda las celdas de la hoja de un área en el periodo ``numero``, todo o nada (D5).

    ``celdas`` es la lista del envío: ``{"estudiante", "competencia", "nivel", "conclusion",
    "base"}``, con ``base`` la nota que la docente vio guardada (``{"nivel", "conclusion"}``)
    o ``None``. Toda validación termina antes de la primera escritura (RNF-011).

    Bloquea la sección, como ``guardar_marcas``: dos guardados van en fila y desmarcar una
    competencia no se cruza con el primer guardado de sus notas. Una celda cuya nota ya es la
    enviada no se escribe (D6). Deja NOTAS_GUARDADAS si creó o cambió alguna (D13).

    Lanza ``PeriodoNoEditable``, ``Periodo.DoesNotExist``, ``InstitucionArea.DoesNotExist``
    (área que la institución no trabaja), ``HojaCambiada``, ``HojaConErrores`` y
    ``NotasCambiadas``. Devuelve ``ResultadoHoja``.
    """
    hoy = hoy or timezone.localdate()
    with transaction.atomic():
        # 1. Sección, año, periodo y área.
        seccion = (
            Seccion.objects.select_for_update(of=("self",))
            .select_related("anio_escolar__institucion")
            .get(pk=seccion.pk)
        )
        if seccion.anio_escolar.estado != AnioEscolar.Estado.ABIERTO:
            raise PeriodoNoEditable
        periodo = Periodo.objects.get(anio_escolar_id=seccion.anio_escolar_id, numero=numero)
        if periodo.fecha_inicio > hoy:
            raise PeriodoNoEditable
        area = InstitucionArea.objects.get(
            institucion_id=seccion.anio_escolar.institucion_id,
            area__codigo_siagie=codigo_area,
            se_trabaja=True,
        )

        # 2. Estructura: cada celda es de la hoja tal como está ahora.
        leidas = _leer_celdas(celdas)
        if not puede_marcar(usuario, seccion, area):
            raise HojaCambiada
        columnas = set(
            CompetenciaPeriodo.objects.filter(
                seccion=seccion,
                periodo=periodo,
                competencia__area_id=area.area_id,
                competencia__activa=True,
            ).values_list("competencia_id", flat=True)
        )
        activos = set(
            seccion.estudiantes.filter(estado=Estudiante.Estado.ACTIVO).values_list("pk", flat=True)
        )
        claves = [clave for clave, *_ in leidas]
        if len(set(claves)) != len(claves) or any(
            estudiante not in activos or competencia not in columnas
            for estudiante, competencia in claves
        ):
            raise HojaCambiada

        # 3 y 4. Escala (RN-001) y conclusión en B y C.
        no_validas, sin_conclusion, enviadas = [], [], []
        for clave, nivel, conclusion, base in leidas:
            nivel = nivel.strip().upper()
            conclusion = conclusion.strip()
            if nivel not in NIVELES:
                no_validas.append(clave)
            elif nivel in CON_CONCLUSION:
                if not CONCLUSION_MINIMA <= len(conclusion) <= CONCLUSION_MAXIMA:
                    sin_conclusion.append(clave)
            else:
                conclusion = ""
            enviadas.append((clave, (nivel, conclusion), base))
        if no_validas or sin_conclusion:
            raise HojaConErrores(no_validas, sin_conclusion)

        # 5. Cambios desde otro dispositivo (D7) e idempotencia (D6).
        actuales = _notas_actuales(periodo, set(claves))
        choques, nuevas, cambiadas = [], [], []
        for clave, enviada, base in enviadas:
            nota = actuales.get(clave)
            actual = (nota.nivel, nota.conclusion_descriptiva) if nota else None
            if actual == enviada:
                continue
            if actual != base:
                choques.append(
                    {
                        "estudiante": clave[0],
                        "competencia": clave[1],
                        "nivel": actual[0] if actual else None,
                        "conclusion": actual[1] if actual else "",
                    }
                )
            elif nota is None:
                nuevas.append((clave, enviada))
            else:
                nota.nivel, nota.conclusion_descriptiva = enviada
                cambiadas.append(nota)
        if choques:
            raise NotasCambiadas(choques)

        # 6. Escritura.
        Calificacion.objects.bulk_create(
            Calificacion(
                estudiante_id=estudiante,
                competencia_id=competencia,
                periodo=periodo,
                nivel=nivel,
                conclusion_descriptiva=conclusion,
                registrado_por=usuario,
            )
            for (estudiante, competencia), (nivel, conclusion) in nuevas
        )
        ahora = timezone.now()
        for nota in cambiadas:
            nota.registrado_por = usuario
            nota.actualizado_en = ahora  # bulk_update no pasa por auto_now
        Calificacion.objects.bulk_update(
            cambiadas,
            ["nivel", "conclusion_descriptiva", "registrado_por", "actualizado_en"],
        )
        pares = sorted((nota.estudiante_id, nota.competencia_id) for nota in cambiadas)
        if nuevas or cambiadas:
            registrar(
                usuario,
                Operacion.NOTAS_GUARDADAS,
                entidad="seccion",
                entidad_id=seccion,
                detalle={
                    "area": codigo_area,
                    "periodo": periodo.numero,
                    "creadas": len(nuevas),
                    "cambiadas": [list(par) for par in pares],
                },
            )
        faltantes = len(notas_faltantes(usuario, seccion, periodo, area))
    return ResultadoHoja(creadas=len(nuevas), cambiadas=pares, faltantes=faltantes)


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
