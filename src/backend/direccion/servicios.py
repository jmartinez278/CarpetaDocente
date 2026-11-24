"""Servicios de la dirección: periodo elegido, estado de las secciones y resumen de la I.E.

Design de US-040, D3 y D4. Solo leen. Una sola función por cifra: el mapa, el resumen, la
portada y el detalle usan estas, para que sus números no se separen (RNF-017). Las funciones
que dependen del día reciben ``hoy`` para que las pruebas lo fijen sin tocar el reloj.
"""

import datetime
from dataclasses import dataclass, field

from django.db.models import Count, Q
from django.http import Http404
from django.utils import timezone

from asistencia import servicios as asistencia
from catalogo.models import InstitucionArea
from cuentas.models import Usuario
from institucion.models import AnioEscolar, Estudiante, Seccion
from institucion.servicios import texto_seccion_corto
from notas import servicios as notas
from repositorio import servicios as repositorio
from repositorio.models import Sesion

SIN_DOCENTE = "SIN_DOCENTE"
SIN_ESTUDIANTES = "SIN_ESTUDIANTES"
ATRASADA = "ATRASADA"
AL_DIA = "AL_DIA"

DEFINICION_AL_DIA = "Al día: sin notas que falten y sin días por completar."


# --- D2. Sección de la dirección ---

_ID_MAXIMO = 2**31


def seccion_de_la_direccion(usuario, id_seccion):
    """La sección ``id_seccion`` del año ABIERTO de la institución de ``usuario`` (Dirección).

    Si no existe, es de otra institución, de un año CERRADO o la pide otro rol: ``Http404``, el
    mismo para todos los casos (la dirección no tiene secciones «ajenas» en su institución y
    otra institución es «inexistente» para ella). Trae el año y la tutora.
    """
    try:
        pk = int(id_seccion)
    except (TypeError, ValueError):
        raise Http404 from None
    if usuario.rol != Usuario.Rol.DIRECCION or usuario.institucion_id is None:
        raise Http404
    if not 0 < pk < _ID_MAXIMO:
        raise Http404
    seccion = (
        Seccion.objects.select_related("anio_escolar", "docente")
        .filter(
            pk=pk,
            anio_escolar__institucion_id=usuario.institucion_id,
            anio_escolar__estado=AnioEscolar.Estado.ABIERTO,
        )
        .first()
    )
    if seccion is None:
        raise Http404
    return seccion


# --- D4. Periodo elegido ---


def _anio_abierto(institucion):
    return AnioEscolar.objects.filter(
        institucion=institucion, estado=AnioEscolar.Estado.ABIERTO
    ).first()


def periodos_del_anio(institucion, hoy):
    """Los periodos del año ABIERTO de la institución con su estado; sin año o sin periodos,
    lista vacía."""
    anio = _anio_abierto(institucion)
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


# --- D9. Portada de la dirección ---

GRADOS = range(1, 7)
COLUMNAS_DEL_MAPA = 4

# Casilla de la miniatura: «o» al día, «x» atrasada, «s» sin docente o sin estudiantes, «v» vacía.
CASILLA_AL_DIA = "o"
CASILLA_ATRASADA = "x"
CASILLA_SIN_TRABAJO = "s"
CASILLA_VACIA = "v"

_CASILLA_DEL_ESTADO = {
    AL_DIA: CASILLA_AL_DIA,
    ATRASADA: CASILLA_ATRASADA,
    SIN_DOCENTE: CASILLA_SIN_TRABAJO,
    SIN_ESTUDIANTES: CASILLA_SIN_TRABAJO,
}


@dataclass
class FilaDelMapa:
    """Un grado de la miniatura de la portada con sus casillas, hasta completar las columnas."""

    grado: int
    casillas: list[str]


@dataclass
class InicioDireccion:
    """Lo que dice la portada de la dirección (spec pantallas-de-inicio, «Inicio de la dirección»).

    ``vigente`` es el bimestre vigente (``PeriodoDeLaSeccion``) o ``None``. Solo con vigente hay
    ``secciones``, ``atrasadas`` y ``mapa``: sin él (sin bimestres, antes del primero, entre dos o
    después del último) la banda no cuenta nada y la miniatura lleva solo la fecha.
    """

    anio: int
    hoy: datetime.date
    hay_periodos: bool
    vigente: object = None
    secciones: int = 0
    atrasadas: int = 0
    mapa: list[FilaDelMapa] = field(default_factory=list)

    @property
    def dia_semana(self):
        return asistencia.DIAS[self.hoy.weekday()]

    @property
    def mes(self):
        return asistencia.MESES[self.hoy.month - 1]

    @property
    def fecha_para_el_lector(self):
        return f"Hoy, {asistencia.texto_dia(self.hoy)}"

    @property
    def hasta(self):
        """El fin del vigente: «18 de diciembre»."""
        fin = self.vigente.fecha_fin
        return f"{fin.day} de {asistencia.MESES[fin.month - 1]}"

    @property
    def de_las_secciones(self):
        """«las 24 secciones» para la frase de la banda; con una, «la sección»."""
        if self.secciones == 1:
            return "la sección"
        return f"las {self.secciones} secciones" if self.secciones else "las secciones"


def _filas_del_mapa(estados):
    por_grado = {grado: [] for grado in GRADOS}
    for estado in estados:
        por_grado.setdefault(estado.seccion.grado, []).append(_CASILLA_DEL_ESTADO[estado.estado])
    return [
        FilaDelMapa(grado, casillas + [CASILLA_VACIA] * (COLUMNAS_DEL_MAPA - len(casillas)))
        for grado, casillas in sorted(por_grado.items())
    ]


def inicio_de_la_direccion(institucion, hoy):
    """La portada de la dirección. Con bimestre vigente, cuatro consultas más para las secciones.

    La pastilla cuenta las atrasadas del vigente (D9); en un bimestre anterior no hay pastilla
    aunque Consolidados lo abra.
    """
    anio = _anio_abierto(institucion)
    periodos = notas.periodos_del_anio_escolar(anio, hoy) if anio is not None else []
    inicio = InicioDireccion(
        anio=anio.anio if anio is not None else hoy.year, hoy=hoy, hay_periodos=bool(periodos)
    )
    inicio.vigente = next((p for p in periodos if p.estado == notas.VIGENTE), None)
    if inicio.vigente is None:
        return inicio
    estados = estado_de_las_secciones(institucion, inicio.vigente.periodo, hoy)
    inicio.secciones = len(estados)
    inicio.atrasadas = sum(e.estado == ATRASADA for e in estados)
    inicio.mapa = _filas_del_mapa(estados)
    return inicio


# --- D6. Sesiones de una sección y docentes de curso del grado ---


def _fecha_de_envio(sesion):
    """El día en que se envió la sesión, en hora de Lima."""
    return timezone.localtime(sesion.creado_en, repositorio.LIMA).date()


def _agrupar_por_dia(sesiones):
    """``{fecha: [sesiones]}`` con las más recientes primero dentro de cada día."""
    por_dia = {}
    for sesion in sesiones:
        por_dia.setdefault(_fecha_de_envio(sesion), []).append(sesion)
    return por_dia


def _texto_corto(fecha):
    """«vie 20 nov»."""
    dia = asistencia.DIAS[fecha.weekday()][:3].lower()
    return f"{dia} {fecha.day} {asistencia.MESES[fecha.month - 1][:3]}"


@dataclass
class DiaDeSesiones(asistencia.Dia):
    """Un día de la semana de Sesiones: ``numero`` de sesiones de la sección y su enlace."""

    numero: int = 0


@dataclass
class SesionesDeLaSeccion:
    """Las sesiones de la tutora de una sección en un periodo (D6) y lo que arma la pestaña.

    Solo estas sesiones alimentan la semana, los números por día, el día por defecto y el
    «N de M días con sesión»; las de los docentes de curso van aparte y no suman a la sección.
    """

    periodo: object
    hoy: datetime.date
    sesiones: list
    por_dia: dict
    dias_de_clase: list

    @property
    def dias_con_sesion(self):
        """Los días de clase hasta hoy en que la tutora envió alguna sesión."""
        return len(set(self.dias_de_clase) & set(self.por_dia))

    @property
    def tope(self):
        """El último día que se puede abrir: hoy, o el fin del periodo si ya terminó."""
        return min(self.periodo.fecha_fin, self.hoy)

    def numero(self, dia):
        return len(self.por_dia.get(dia, []))

    def del_dia(self, dia):
        return self.por_dia.get(dia, [])

    def _se_abre(self, dia):
        """Un día de clase dentro del periodo y no posterior a hoy."""
        return asistencia.es_dia_de_clases(dia) and self.periodo.fecha_inicio <= dia <= self.tope

    def dia_elegido(self, pedido):
        """El día que abre la pestaña: el pedido (``?dia=AAAA-MM-DD``) si se puede abrir; si no,
        hoy con sesiones de la sección, o el último día con sesiones, o el último día de clase.

        Un día con solo una sesión de un docente de curso no cuenta: no es de la sección.
        """
        try:
            dia = datetime.date.fromisoformat(pedido)
        except (TypeError, ValueError):
            dia = None
        if dia is not None and self._se_abre(dia):
            return dia
        if self.hoy in self.por_dia and self._se_abre(self.hoy):
            return self.hoy
        con_sesiones = [d for d in self.por_dia if self._se_abre(d)]
        if con_sesiones:
            return max(con_sesiones)
        return self.dias_de_clase[-1] if self.dias_de_clase else self.periodo.fecha_inicio

    def semana(self, elegido, url_de=datetime.date.isoformat):
        """El selector de la semana de ``elegido``, lunes a viernes, con ``url_de(fecha)`` en
        cada día y flechas a la semana anterior y siguiente mientras tengan días del periodo."""
        un_dia = datetime.timedelta(days=1)
        lunes = elegido - datetime.timedelta(days=elegido.weekday())
        dias = []
        for n in range(5):
            fecha = lunes + n * un_dia
            disponible = self._se_abre(fecha)
            dias.append(
                DiaDeSesiones(
                    fecha=fecha,
                    es_hoy=fecha == self.hoy,
                    elegido=fecha == elegido,
                    disponible=disponible,
                    url=url_de(fecha) if disponible else None,
                    numero=self.numero(fecha),
                )
            )
        hay_anterior = lunes - 3 * un_dia >= self.periodo.fecha_inicio
        hay_siguiente = lunes + 7 * un_dia <= self.tope
        return asistencia.Semana(
            dias=dias,
            anterior=self._flecha(elegido, -7, hay_anterior, url_de),
            siguiente=self._flecha(elegido, 7, hay_siguiente, url_de),
        )

    def _flecha(self, elegido, dias, hay_semana, url_de):
        """El mismo día de la semana vecina, ajustado al periodo y a un día de clase."""
        if not hay_semana:
            return None
        destino = elegido + datetime.timedelta(days=dias)
        destino = min(max(destino, self.periodo.fecha_inicio), self.tope)
        while not asistencia.es_dia_de_clases(destino):
            destino -= datetime.timedelta(days=1)
        return url_de(destino)


def sesiones_de_la_seccion(seccion, periodo, hoy):
    """Las sesiones de la tutora de ``seccion`` para su grado, enviadas dentro de ``periodo``.

    Una sola consulta: sin el material de referencia, compartidas o no, por fecha de envío en
    Lima. Sin tutora no hay sesiones. ``periodo`` es el ``Periodo`` del modelo.
    """
    if seccion.docente_id is None:
        sesiones = []
    else:
        sesiones = list(
            repositorio.sesiones_propias_del_grado(
                seccion.anio_escolar.institucion_id,
                seccion.grado,
                periodo.fecha_inicio,
                periodo.fecha_fin,
            ).filter(autor_id=seccion.docente_id)
        )
    return SesionesDeLaSeccion(
        periodo=periodo,
        hoy=hoy,
        sesiones=sesiones,
        por_dia=_agrupar_por_dia(sesiones),
        dias_de_clase=asistencia.dias_de_clase(periodo, hoy),
    )


@dataclass
class DocenteDeCurso:
    """Un docente de curso con las sesiones de su área para el grado en el periodo (D6)."""

    autor: Usuario
    area: object
    sesiones: list
    por_dia: dict

    @property
    def dias_con_sesion(self):
        return len(self.por_dia)

    @property
    def ultima(self):
        return max(self.por_dia)

    @property
    def texto_dias(self):
        """«2 días con sesión · Última: vie 20 nov»."""
        n = self.dias_con_sesion
        dias = "1 día con sesión" if n == 1 else f"{n} días con sesión"
        return f"{dias} · Última: {_texto_corto(self.ultima)}"

    def del_dia(self, dia):
        return self.por_dia.get(dia, [])


def sesiones_de_curso_del_grado(institucion, grado, periodo):
    """Los docentes de curso con sesiones de ``grado`` en ``periodo``, por apellidos (D6).

    Son las sesiones de las áreas a cargo del docente de curso en la institución, de cualquier
    autor, sin importar la sección: nunca se atribuyen a una. Una sola consulta.
    """
    a_cargo = InstitucionArea.objects.filter(
        institucion=institucion, a_cargo_docente_curso=True
    ).values("area_id")
    sesiones = repositorio.sesiones_propias_del_grado(
        institucion.pk, grado, periodo.fecha_inicio, periodo.fecha_fin
    ).filter(area_id__in=a_cargo)
    por_docente = {}
    for sesion in sesiones:
        por_docente.setdefault((sesion.autor, sesion.area), []).append(sesion)
    docentes = [
        DocenteDeCurso(autor, area, lista, _agrupar_por_dia(lista))
        for (autor, area), lista in por_docente.items()
    ]
    return sorted(
        docentes,
        key=lambda d: (d.autor.last_name, d.autor.first_name, d.autor.pk, d.area.nombre),
    )
