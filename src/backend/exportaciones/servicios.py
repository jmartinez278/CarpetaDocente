"""Servicios de exportaciones: completar la plantilla de notas del SIAGIE (US-024/025).

Toda regla y toda escritura en la base: reconocer la plantilla (design D2, D6), resolver su
sección (D3, D5), cruzar estudiantes (D7), llenar y contar (D8), registrar (D11) y borrar una
equivalencia (D13). El libro se lee y escribe con ``siagie``, en memoria: ni el archivo ni los
nombres de la plantilla se guardan (decisión 2, Ley 29733).
"""

import re
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import Prefetch

from actividad.models import Operacion
from actividad.servicios import registrar
from catalogo.models import Area, Competencia, InstitucionArea
from exportaciones import siagie
from exportaciones.models import EquivalenciaSeccion

# La vista las atrapa desde aquí junto con las de este módulo.
from exportaciones.siagie import ArchivoDemasiadoGrande, PlantillaNoReconocida  # noqa: F401
from institucion.models import AnioEscolar, Institucion, Periodo, Seccion
from notas.models import Calificacion
from notas.servicios import CON_CONCLUSION, notas_faltantes

SECCION_NO_VALIDA = "La sección elegida no es válida. Elige una de la lista."
SIN_NOTAS = "No hay notas para completar en este periodo"
EQUIVALENCIA_INEXISTENTE = "Esta equivalencia ya no existe."
COMPLETADA_GRANDE = (
    "La plantilla completada supera los 3 MB y no se puede descargar. No se guardó ningún cambio."
)
COMPLETADA = "Plantilla completada"
CON_OBSERVACIONES = "Plantilla completada con observaciones"
PERIODO_SIAGIE = re.compile(r"^B([1-4])$")
# Lo que cabe en la equivalencia: más largo no es la plantilla (y no llega a la base).
CODIGO_SECCION_MAXIMO = EquivalenciaSeccion._meta.get_field("codigo_siagie").max_length
NOMBRE_SECCION_MAXIMO = EquivalenciaSeccion._meta.get_field("nombre_siagie").max_length

# De dónde salió la sección del resumen (D5, D13).
POR_EQUIVALENCIA = "equivalencia"
POR_NOMBRE = "nombre"
NUEVA = "nueva"


class SinSeccionesDelGrado(Exception):
    """La institución no tiene secciones del grado en el año de la plantilla."""

    def __init__(self, grado, anio):
        super().__init__(f"Tu I.E. no tiene secciones de {grado}.º grado en {anio}.")


class EligeSeccion(Exception):
    """La sección no se resuelve sola: la dirección elige entre ``opciones`` (D3)."""

    def __init__(self, plantilla, opciones):
        super().__init__("Elige la sección")
        self.plantilla = plantilla
        self.opciones = opciones


class SeccionNoValida(Exception):
    """La sección elegida no está entre las opciones o ya es de otra equivalencia (D3, D5)."""

    def __init__(self):
        super().__init__(SECCION_NO_VALIDA)


class EquivalenciaInexistente(Exception):
    """La equivalencia no es de la institución de quien la borra o ya se borró (D13)."""

    def __init__(self):
        super().__init__(EQUIVALENCIA_INEXISTENTE)


class SinNotasEnElPeriodo(Exception):
    """La sección no tiene ninguna nota en el periodo: no se devuelve archivo (D8)."""

    def __init__(self):
        super().__init__(SIN_NOTAS)


class CompletadaDemasiadoGrande(Exception):
    """La completada pasa de ``siagie.LIMITE_BYTES``: en base64 no cabría en la respuesta de
    Vercel, así que nada se guarda (D4, D9)."""

    def __init__(self):
        super().__init__(COMPLETADA_GRANDE)


# --- D2 y D6. Reconocer ---


@dataclass
class HojaReconocida:
    """Una hoja de área con su ``Area`` y la competencia de cada número de la fila 1."""

    hoja: siagie.HojaDeArea
    area: Area
    competencias: dict[int, Competencia]


@dataclass
class Plantilla:
    """La plantilla reconocida: el libro y lo que corresponde en la institución."""

    libro: siagie.Libro
    institucion: Institucion
    anio_escolar: AnioEscolar
    periodo: Periodo
    hojas: list[HojaReconocida]

    @property
    def parametros(self):
        return self.libro.parametros

    @property
    def grado(self):
        return self.parametros.grado

    @property
    def nombre_siagie(self):
        """El nombre de la sección del SIAGIE como se guarda en la equivalencia."""
        return siagie.clave(self.parametros.nombre_seccion)


def _hojas_reconocidas(libro):
    """Cada hoja con su área del catálogo y sus competencias por número (D6). Dos consultas."""
    areas = {
        area.codigo_siagie: area
        for area in Area.objects.filter(
            codigo_siagie__in={hoja.codigo for hoja in libro.hojas}
        ).prefetch_related(
            Prefetch(
                "competencias",
                queryset=Competencia.objects.filter(activa=True).order_by("orden", "pk"),
                to_attr="activas",
            )
        )
    }
    reconocidas = []
    for hoja in libro.hojas:
        area = areas.get(hoja.codigo)
        if area is None:
            raise PlantillaNoReconocida
        if any(numero > len(area.activas) for numero in hoja.competencias):
            raise PlantillaNoReconocida
        reconocidas.append(
            HojaReconocida(
                hoja=hoja,
                area=area,
                competencias={numero: area.activas[numero - 1] for numero in hoja.competencias},
            )
        )
    return reconocidas


def reconocer(usuario, libro):
    """La ``Plantilla`` de ``libro`` en la institución de ``usuario``, o
    ``PlantillaNoReconocida`` (D2): código modular y anexo de la institución, un año escolar
    suyo, un bimestre de ese año y hojas de áreas y competencias del catálogo."""
    institucion = getattr(usuario, "institucion", None)
    parametros = libro.parametros
    if (
        institucion is None
        or not (institucion.codigo_modular or "").strip()
        or institucion.codigo_modular.strip() != parametros.codigo_modular
        or institucion.anexo != parametros.anexo
        or institucion.organizacion_periodos != Institucion.OrganizacionPeriodos.BIMESTRE
    ):
        raise PlantillaNoReconocida
    coincidencia = PERIODO_SIAGIE.match(parametros.periodo)
    if (
        coincidencia is None
        or len(parametros.codigo_seccion) > CODIGO_SECCION_MAXIMO
        or len(siagie.clave(parametros.nombre_seccion)) > NOMBRE_SECCION_MAXIMO
    ):
        raise PlantillaNoReconocida
    periodo = (
        Periodo.objects.select_related("anio_escolar")
        .filter(
            anio_escolar__institucion=institucion,
            anio_escolar__anio=parametros.anio,
            numero=int(coincidencia.group(1)),
        )
        .first()
    )
    if periodo is None:
        raise PlantillaNoReconocida
    return Plantilla(
        libro=libro,
        institucion=institucion,
        anio_escolar=periodo.anio_escolar,
        periodo=periodo,
        hojas=_hojas_reconocidas(libro),
    )


# --- D3 y D5. La sección ---


@dataclass
class SeccionResuelta:
    """La sección de la I.E., de dónde salió y su equivalencia guardada, si salió de una."""

    seccion: Seccion
    origen: str
    equivalencia: EquivalenciaSeccion | None = None


def _como_id(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def resolver_seccion(plantilla, seccion_id=None):
    """La sección de la plantilla (D5): 1) su equivalencia guardada; 2) la única del grado con
    el mismo nombre normalizado; 3) la elegida (``seccion_id``) entre las del grado sin otra
    equivalencia. Sin elección, ``EligeSeccion``. Una elección fuera de la lista, o distinta de
    lo que resuelven 1 o 2, es ``SeccionNoValida``. No guarda nada."""
    secciones = list(
        Seccion.objects.filter(anio_escolar=plantilla.anio_escolar, grado=plantilla.grado)
        .select_related("equivalencia_siagie")
        .order_by("nombre", "pk")
    )
    if not secciones:
        raise SinSeccionesDelGrado(plantilla.grado, plantilla.anio_escolar.anio)
    resuelta = None
    equivalencia = EquivalenciaSeccion.objects.filter(
        anio_escolar=plantilla.anio_escolar,
        grado=plantilla.grado,
        codigo_siagie=plantilla.parametros.codigo_seccion,
        nombre_siagie=plantilla.nombre_siagie,
    ).first()
    seccion = next((s for s in secciones if s.pk == getattr(equivalencia, "seccion_id", 0)), None)
    if seccion is not None:
        resuelta = SeccionResuelta(seccion, POR_EQUIVALENCIA, equivalencia)
    else:
        por_nombre = [s for s in secciones if siagie.clave(s.nombre) == plantilla.nombre_siagie]
        if len(por_nombre) == 1:
            resuelta = SeccionResuelta(por_nombre[0], POR_NOMBRE)
    if seccion_id is None:
        if resuelta is None:
            opciones = [s for s in secciones if not hasattr(s, "equivalencia_siagie")]
            raise EligeSeccion(plantilla, opciones)
        return resuelta
    elegida = _como_id(seccion_id)
    if resuelta is not None:
        if elegida != resuelta.seccion.pk:
            raise SeccionNoValida
        return resuelta
    for seccion in secciones:
        if seccion.pk == elegida and not hasattr(seccion, "equivalencia_siagie"):
            return SeccionResuelta(seccion, NUEVA)
    raise SeccionNoValida


def guardar_equivalencia(usuario, plantilla, seccion):
    """Guarda la equivalencia elegida, dentro del ``atomic()`` de quien llama (D5).

    Una carrera (otra sesión la guardó a la vez) da ``IntegrityError`` en un *savepoint*: si
    la guardada apunta a la misma sección se sigue con ella; si no, ``SeccionNoValida``.
    """
    campos = {
        "anio_escolar": plantilla.anio_escolar,
        "grado": plantilla.grado,
        "codigo_siagie": plantilla.parametros.codigo_seccion,
        "nombre_siagie": plantilla.nombre_siagie,
    }
    try:
        with transaction.atomic():
            return EquivalenciaSeccion.objects.create(seccion=seccion, creado_por=usuario, **campos)
    except IntegrityError:
        existente = EquivalenciaSeccion.objects.filter(**campos).first()
        if existente is not None and existente.seccion_id == seccion.pk:
            return existente
        raise SeccionNoValida from None


# --- D7. Cruce de estudiantes ---


def _indice_de_estudiantes(seccion):
    """Clave de nombre → id de estudiante, de todos los estados; ``None`` si la clave es de dos
    estudiantes (homónimos normalizados). Cada estudiante entra con coma («APELLIDOS,NOMBRES»)
    y sin ella («APELLIDOS NOMBRES»), para las filas que no la traen."""
    indice = {}
    for estudiante_id, apellidos, nombres in seccion.estudiantes.values_list(
        "pk", "apellidos", "nombres"
    ):
        for texto in (f"{apellidos},{nombres}", f"{apellidos} {nombres}"):
            clave = siagie.clave(texto)
            indice[clave] = estudiante_id if clave not in indice else None
    return indice


# --- D8. Llenado y conteos ---


@dataclass
class Resumen:
    """Lo que ve la dirección y la descarga. ``no_encontrados`` va solo en la respuesta (D4):
    nunca se guarda ni se registra. ``equivalencia_id``, solo si la sección salió de una."""

    seccion: Seccion
    periodo: Periodo
    grado_siagie: int
    nombre_siagie: str
    encontrados: int
    no_encontrados: list[str]
    faltantes: int
    reemplazadas: int
    equivalencia_id: int | None
    contenido: bytes

    @property
    def anio(self):
        return self.periodo.anio_escolar.anio

    @property
    def observaciones(self):
        return bool(self.no_encontrados) or self.faltantes > 0

    @property
    def titulo(self):
        return CON_OBSERVACIONES if self.observaciones else COMPLETADA


def _notas_del_periodo(seccion, periodo):
    """Una consulta: ``{(estudiante_id, competencia_id): (nivel, conclusión)}``."""
    return {
        (estudiante_id, competencia_id): (nivel, conclusion)
        for estudiante_id, competencia_id, nivel, conclusion in Calificacion.objects.filter(
            periodo=periodo, estudiante__seccion=seccion
        ).values_list("estudiante_id", "competencia_id", "nivel", "conclusion_descriptiva")
    }


def _faltantes(seccion, periodo):
    """Las notas faltantes de la sección con la regla de la hoja de la docente (decisión 8):
    las de su tutora en las áreas que se trabajan. Sin docente de aula, cero."""
    if seccion.docente is None:
        return 0
    areas = InstitucionArea.objects.filter(
        institucion_id=seccion.anio_escolar.institucion_id, se_trabaja=True
    )
    return sum(len(notas_faltantes(seccion.docente, seccion, periodo, ia)) for ia in areas)


def _llenar(plantilla, seccion, notas):
    """Escribe las notas de las filas encontradas (D8). Devuelve los estudiantes encontrados,
    los nombres no encontrados (sin repetir, en orden de aparición) y las celdas reemplazadas."""
    indice = _indice_de_estudiantes(seccion)
    encontrados = set()
    no_encontrados = {}
    reemplazadas = 0
    for reconocida in plantilla.hojas:
        hoja = reconocida.hoja
        for fila, nombre in hoja.filas:
            estudiante_id = indice.get(siagie.clave(nombre))
            if estudiante_id is None:
                no_encontrados.setdefault(siagie.clave(nombre), nombre)
                continue
            encontrados.add(estudiante_id)
            for numero, competencia in reconocida.competencias.items():
                nota = notas.get((estudiante_id, competencia.pk))
                if nota is None:
                    continue
                nivel, conclusion = nota
                columna = hoja.competencias[numero]
                texto = conclusion if nivel in CON_CONCLUSION else None
                reemplazadas += plantilla.libro.escribir(hoja.nombre, fila, columna, nivel)
                reemplazadas += plantilla.libro.escribir(hoja.nombre, fila, columna + 1, texto)
    return len(encontrados), list(no_encontrados.values()), reemplazadas


def completar_plantilla(usuario, contenido, seccion_id=None):
    """Reconoce la plantilla, resuelve su sección, la llena y registra (D1).

    Devuelve el ``Resumen`` o lanza ``ArchivoDemasiadoGrande``, ``PlantillaNoReconocida``,
    ``SinSeccionesDelGrado``, ``EligeSeccion``, ``SeccionNoValida``, ``SinNotasEnElPeriodo`` o
    ``CompletadaDemasiadoGrande``. Guardar la equivalencia, comprobar las notas, medir la
    completada y registrar van en un ``atomic()``: sin notas, o si la completada no cabe en la
    respuesta, la equivalencia nueva no queda (D5).
    """
    plantilla = reconocer(usuario, siagie.abrir(contenido))
    resuelta = resolver_seccion(plantilla, seccion_id)
    seccion, periodo = resuelta.seccion, plantilla.periodo
    with transaction.atomic():
        if resuelta.origen == NUEVA:
            resuelta.equivalencia = guardar_equivalencia(usuario, plantilla, seccion)
        notas = _notas_del_periodo(seccion, periodo)
        if not notas:
            raise SinNotasEnElPeriodo
        encontrados, no_encontrados, reemplazadas = _llenar(plantilla, seccion, notas)
        faltantes = _faltantes(seccion, periodo)
        contenido = plantilla.libro.guardar()
        if len(contenido) > siagie.LIMITE_BYTES:
            raise CompletadaDemasiadoGrande
        registrar(
            usuario,
            Operacion.PLANTILLA_SIAGIE_COMPLETADA,
            entidad="seccion",
            entidad_id=seccion,
            detalle={
                "periodo": periodo.numero,
                "anio": plantilla.anio_escolar.anio,
                "encontrados": encontrados,
                "no_encontrados": len(no_encontrados),
                "faltantes": faltantes,
                "reemplazadas": reemplazadas,
                "equivalencia": resuelta.origen == NUEVA,
            },
        )
    return Resumen(
        seccion=seccion,
        periodo=periodo,
        grado_siagie=plantilla.grado,
        nombre_siagie=plantilla.parametros.nombre_seccion,
        encontrados=encontrados,
        no_encontrados=no_encontrados,
        faltantes=faltantes,
        reemplazadas=reemplazadas,
        equivalencia_id=resuelta.equivalencia.pk if resuelta.equivalencia else None,
        contenido=contenido,
    )


# --- D13. Corregir la equivalencia ---


def borrar_equivalencia(usuario, equivalencia_id):
    """Borra la equivalencia de la institución de ``usuario`` y registra
    EQUIVALENCIA_SECCION_BORRADA en la misma transacción (D13). Si no es de su institución o ya
    no existe, ``EquivalenciaInexistente`` sin entrada. Devuelve la equivalencia borrada (para
    el aviso de la vista)."""
    institucion_id = getattr(usuario, "institucion_id", None)
    equivalencia_id = _como_id(equivalencia_id)
    with transaction.atomic():
        equivalencia = (
            EquivalenciaSeccion.objects.select_for_update()
            .select_related("anio_escolar")
            .filter(pk=equivalencia_id, anio_escolar__institucion_id=institucion_id)
            .first()
            if institucion_id is not None and equivalencia_id is not None
            else None
        )
        if equivalencia is None:
            raise EquivalenciaInexistente
        seccion_id = equivalencia.seccion_id
        detalle = {"anio": equivalencia.anio_escolar.anio, "grado": equivalencia.grado}
        equivalencia.delete()
        registrar(
            usuario,
            Operacion.EQUIVALENCIA_SECCION_BORRADA,
            entidad="seccion",
            entidad_id=seccion_id,
            detalle=detalle,
        )
    return equivalencia
