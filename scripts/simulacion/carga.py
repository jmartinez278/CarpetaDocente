"""Carga de la corrida principal en la app (G3): sim01…sim24 en la institución simulada.

Datos simulados: nada de lo que carga este script es real. Lleva a la base local la ventana O2
(``o2.ventana_semanas`` semanas que terminan en ``o2.fecha_fin``) de las 24 docentes de la
corrida principal, con los mismos rasgos que ``medicion.simular`` (semilla principal):

- asistencia de cada día de clase: marcado masivo y luego las excepciones; en diferido, con
  ``hoy`` posterior a la fecha (queda como corrección) y con días olvidados;
- notas del bimestre en curso, una hoja por área de la tutora, con B y C con conclusión, y a
  veces una corrección A → AD;
- sesiones enviadas con un Word ficticio, Poisson(``autorregistro.sesiones_semana``) por semana.

Todo pasa por los servicios de la app (``asistencia.marcar``, ``notas.guardar_hoja``,
``repositorio.enviar_sesion``) con ``hoy`` simulado. Después de cada llamada, la fecha y hora
simuladas se fijan en ``RegistroActividad.fecha_hora`` y en las marcas de tiempo de lo que creó,
para que «Indicadores por semana» cuente las semanas simuladas.

La base muestra **conductas, no errores**: los conteos E1–E4 y los tiempos del Cap. IV salen de
``medicion.py``, no de aquí. Las constantes de relleno de abajo **no entran al análisis**.

La carga usa su propio generador (el cuarto hijo de la semilla principal): no cambia O1, O2 ni
las réplicas. La institución 1 y la demo no se tocan. Solo con DEBUG y ``--confirmar``.

Uso (con la base local arriba):

    SIM_CLAVE='<clave>' uv run python scripts/simulacion/carga.py cargar --confirmar
    uv run python scripts/simulacion/carga.py quitar --confirmar
"""

# ruff: noqa: E402  (Django se configura antes de importar los modelos, también al correr suelto)

import argparse
import datetime
import logging
import os
import random
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

# Al importarse, preparar_rutas configura Django: va antes que los modelos.
from simulacion import preparar_rutas as base

base._preparar_django()

from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, transaction
from django.db.models import Max

from actividad.models import RegistroActividad
from actividad.servicios import LIMA
from asistencia import servicios as asistencia
from asistencia.models import Asistencia, Jornada
from catalogo.models import InstitucionArea
from cuentas.models import Usuario
from institucion import servicios
from institucion.models import Estudiante, Periodo, Seccion
from notas import servicios as notas
from notas.models import Calificacion, CompetenciaPeriodo
from repositorio import servicios as repositorio
from repositorio.ejemplos import docx_con_texto
from repositorio.models import TIPO_DOCX, Sesion
from simulacion import docentes as modulo_docentes
from simulacion import parametros

logger = logging.getLogger(__name__)

ORIGEN = "Datos simulados"

# ── Constantes de relleno: solo para poblar la base; NO ENTRAN AL ANÁLISIS ───────────────────
# Horas (Lima) en que queda cada acción. La asistencia en el momento, al empezar la jornada; lo
# demás, de noche, como lo cuenta la entrevista (en casa o al terminar el día).
HORA_ASISTENCIA_MOMENTO = datetime.time(8)
HORA_ASISTENCIA_DIFERIDO = datetime.time(19)
HORA_NOTAS = datetime.time(20)
HORA_CORRECCION = datetime.time(20, 30)
HORA_SESION = datetime.time(21)
# Días de retraso de la asistencia en diferido (al azar, de 1 a 3), sin pasar de la ventana.
RETRASO_DIFERIDO = (1, 3)
# Reparto de las excepciones de asistencia (los que no tienen «Asistió»).
EXCEPCIONES = (
    (Asistencia.Estado.FALTO, 0.5),
    (Asistencia.Estado.TARDE, 0.3),
    (Asistencia.Estado.JUSTIFICADO, 0.2),
)
NOTA_JUSTIFICADO = "Justificación simulada"
# Entre las notas sin conclusión, la parte que es AD (el resto, A); entre B y C, la parte de C.
PROPORCION_AD = 0.2
PROPORCION_C = 0.3
CONCLUSION_BASE = "Conclusión descriptiva simulada para la carga de G3. "
# ─────────────────────────────────────────────────────────────────────────────────────────────

ESPACIO_SESIONES = uuid.UUID("5f0c3a52-6c55-4d6e-9a8e-2b1f0e7d3c41")  # ids reproducibles


@dataclass
class ResumenCarga:
    docentes: int = 0
    estudiantes: int = 0
    jornadas: int = 0
    notas: int = 0
    sesiones: int = 0

    @property
    def texto(self):
        return (
            f"{ORIGEN}: {self.docentes} docentes, {self.estudiantes} estudiantes, "
            f"{self.jornadas} jornadas, {self.notas} notas y {self.sesiones} sesiones."
        )


@dataclass
class ResumenQuitar:
    estudiantes: int = 0
    entradas: int = 0


# ── la corrida principal ─────────────────────────────────────────────────────────────────────


def _hijos(semilla):
    """Los generadores de la corrida: docentes, O1 y O2 (como ``medicion``) y el de la carga."""
    return [np.random.default_rng(s) for s in np.random.SeedSequence(semilla).spawn(4)]


def docentes_principales(valores, semilla):
    """Las docentes de ``medicion.simular`` con esa semilla: el primer hijo de la semilla."""
    return modulo_docentes.generar(valores, _hijos(semilla)[0])


def dias_de_la_ventana(valores):
    """Días de lunes a viernes de las ``ventana_semanas`` semanas que terminan en ``fecha_fin``."""
    fin = datetime.date.fromisoformat(str(valores["o2"]["fecha_fin"]))
    lunes = fin - datetime.timedelta(days=fin.weekday())
    inicio = lunes - datetime.timedelta(weeks=valores["o2"]["ventana_semanas"] - 1)
    dias = []
    dia = inicio
    while dia <= fin:
        if asistencia.es_dia_de_clases(dia):
            dias.append(dia)
        dia += datetime.timedelta(days=1)
    return dias


# ── guardas ──────────────────────────────────────────────────────────────────────────────────


def _exigir_confirmar(confirmar):
    if not confirmar:
        raise base.BaseNoSegura(
            "Falta --confirmar: la carga y el retiro de la simulación lo piden."
        )


def _revisar_cuentas(institucion, usuarios):
    otras = sorted(
        Usuario.objects.filter(username__in=usuarios)
        .exclude(institucion=institucion)
        .values_list("username", flat=True)
    )
    if otras:
        raise base.BaseNoSegura(
            f"Ya existen en otra institución: {', '.join(otras)}. No se reutilizan."
        )


def _revisar_vacia(institucion):
    if Estudiante.objects.filter(seccion__anio_escolar__institucion=institucion).exists():
        raise base.BaseNoSegura(
            "Ya hay una carga de la simulación (secciones con estudiantes). Corre primero "
            "«quitar --confirmar»."
        )


# ── la fecha simulada ────────────────────────────────────────────────────────────────────────


def _momento(dia, hora):
    """La fecha y hora simuladas, en hora de Lima (como las lee «Indicadores por semana»)."""
    return datetime.datetime.combine(dia, hora, tzinfo=LIMA)


@contextmanager
def _a_la_fecha(cuenta, momento):
    """Las entradas de ``cuenta`` que deja el bloque quedan en ``momento``.

    ``QuerySet.update()`` no pasa por el ``save`` de solo lectura del modelo; la base aún no lo
    impide (EN-04). Solo toca las entradas nuevas de esa cuenta de la simulación.
    """
    ultimo = RegistroActividad.objects.aggregate(m=Max("id"))["m"] or 0
    yield
    RegistroActividad.objects.filter(usuario=cuenta, id__gt=ultimo).update(fecha_hora=momento)


def _fijar(consulta, **campos):
    """``update`` por ids leídos antes.

    Un ``UPDATE … WHERE id IN (SELECT … JOIN …)`` sobre tablas recién llenadas, sin
    estadísticas, tardaba decenas de segundos por llamada.
    """
    ids = list(consulta.values_list("pk", flat=True))
    consulta.model.objects.filter(pk__in=ids).update(**campos)


# ── las cuentas y las secciones ──────────────────────────────────────────────────────────────


def _cuenta(institucion, docente, clave):
    cuenta = Usuario.objects.filter(username=docente.usuario).first()
    if cuenta is None:
        return Usuario.objects.create_user(
            username=docente.usuario,
            password=clave,
            rol=Usuario.Rol.DOCENTE,
            institucion=institucion,
            es_demo=False,
            first_name="Docente",
            last_name=f"Simulada {docente.codigo}",
        )
    cuenta.is_active = True
    cuenta.debe_cambiar_password = False
    cuenta.set_password(clave)
    cuenta.save()
    return cuenta


def _seccion(institucion, docente, cuenta, fin):
    seccion = Seccion.objects.select_for_update(of=("self",)).get(
        anio_escolar__institucion=institucion,
        anio_escolar__anio=base.ANIO,
        grado=docente.grado,
        nombre=docente.seccion,
    )
    seccion.docente = cuenta
    seccion.save()
    # Los mismos nombres que en preparar_rutas para esa sección.
    azar = random.Random(f"sim-{docente.grado}{docente.seccion}")  # noqa: S311
    _, errores = servicios.importar_lista_sin_registro(
        seccion, base._lista(azar, docente.n_estudiantes)
    )
    if errores:
        raise ValidationError([error.titulo for error in errores])
    empezados = Periodo.objects.filter(anio_escolar=seccion.anio_escolar, fecha_inicio__lte=fin)
    notas.marcar_todo_sin_registro(seccion, list(empezados))
    return seccion


# ── asistencia ───────────────────────────────────────────────────────────────────────────────


def _asistencia(seccion, cuenta, docente, dias, valores, rng):
    """Cada día de la ventana: marcado masivo y luego las excepciones. Devuelve las jornadas."""
    tasa = valores["poblacion"]["tasa_excepciones_asistencia"]
    olvido = valores["errores_o2"]["asistencia"]["olvida_dia"]
    fin = dias[-1]
    estados = [estado for estado, _ in EXCEPCIONES]
    pesos = [peso for _, peso in EXCEPCIONES]
    ids = list(seccion.estudiantes.order_by("apellidos", "nombres").values_list("pk", flat=True))
    jornadas = 0
    for dia in dias:
        if docente.modalidad == "diferido":
            if rng.random() < olvido:
                continue
            retraso = int(rng.integers(RETRASO_DIFERIDO[0], RETRASO_DIFERIDO[1] + 1))
            hoy = min(dia + datetime.timedelta(days=retraso), fin)
            momento = _momento(hoy, HORA_ASISTENCIA_DIFERIDO)
        else:
            hoy = dia
            momento = _momento(dia, HORA_ASISTENCIA_MOMENTO)
        excepciones = [pk for pk in ids if rng.random() < tasa]
        with _a_la_fecha(cuenta, momento):
            asistencia.marcar_restantes(seccion, ids, dia, cuenta, hoy=hoy)
            for pk in excepciones:
                estado = estados[int(rng.choice(len(estados), p=pesos))]
                nota = NOTA_JUSTIFICADO if estado == Asistencia.Estado.JUSTIFICADO else ""
                asistencia.marcar(seccion, pk, dia, estado, nota, cuenta, hoy=hoy)
        Jornada.objects.filter(seccion=seccion, fecha=dia).update(creado_en=momento)
        _fijar(
            Asistencia.objects.filter(jornada__seccion=seccion, jornada__fecha=dia),
            actualizado_en=momento,
        )
        jornadas += 1
    return jornadas


# ── notas ────────────────────────────────────────────────────────────────────────────────────


def _conclusion(caracteres):
    texto = CONCLUSION_BASE * (caracteres // len(CONCLUSION_BASE) + 1)
    return texto[:caracteres].rstrip().ljust(caracteres, ".")


def _nivel(rng, proporcion_bc):
    if rng.random() < proporcion_bc:
        return "C" if rng.random() < PROPORCION_C else "B"
    return "AD" if rng.random() < PROPORCION_AD else "A"


def _areas_de_la_tutora(seccion, periodo, de_curso):
    """Las áreas que marca la tutora en el periodo, con sus competencias marcadas."""
    filas = (
        InstitucionArea.objects.filter(
            institucion_id=seccion.anio_escolar.institucion_id,
            se_trabaja=True,
            a_cargo_docente_curso=False,
        )
        .exclude(area__codigo_siagie__in=de_curso)
        .select_related("area")
        .order_by("area__orden", "area__pk")
    )
    areas = []
    for fila in filas:
        competencias = list(
            CompetenciaPeriodo.objects.filter(
                seccion=seccion,
                periodo=periodo,
                competencia__area_id=fila.area_id,
                competencia__activa=True,
            )
            .order_by("competencia__orden", "competencia_id")
            .values_list("competencia_id", flat=True)
        )
        if competencias:
            areas.append((fila.area, competencias))
    return areas


def _notas(seccion, cuenta, dias, valores, rng):
    """Una hoja por área de la tutora en el periodo de la ventana; a veces una corrección."""
    p = valores["poblacion"]
    proporcion_bc, caracteres = p["proporcion_conclusion_notas"], p["caracteres_conclusion"]
    prob_correccion = valores["o1"]["corregir_nota"]["probabilidad"]
    de_curso = valores["catalogo"]["areas_de_docente_de_curso"]
    periodo = Periodo.objects.get(
        anio_escolar=seccion.anio_escolar,
        fecha_inicio__lte=dias[-1],
        fecha_fin__gte=dias[-1],
    )
    ids = list(seccion.estudiantes.order_by("apellidos", "nombres").values_list("pk", flat=True))
    conclusion = _conclusion(caracteres)
    creadas = 0
    corregibles = []
    for area, competencias in _areas_de_la_tutora(seccion, periodo, de_curso):
        dia = dias[int(rng.integers(len(dias)))]
        celdas = []
        for estudiante in ids:
            for competencia in competencias:
                nivel = _nivel(rng, proporcion_bc)
                texto = conclusion if nivel in notas.CON_CONCLUSION else ""
                celdas.append(
                    {
                        "estudiante": estudiante,
                        "competencia": competencia,
                        "nivel": nivel,
                        "conclusion": texto,
                        "base": None,
                    }
                )
                if nivel == "A":
                    corregibles.append((area, dia, estudiante, competencia))
        momento = _momento(dia, HORA_NOTAS)
        with _a_la_fecha(cuenta, momento):
            resultado = notas.guardar_hoja(
                cuenta, seccion, periodo.numero, area.codigo_siagie, celdas, hoy=dia
            )
        _fijar(
            Calificacion.objects.filter(
                estudiante_id__in=ids, periodo=periodo, competencia_id__in=competencias
            ),
            creado_en=momento,
            actualizado_en=momento,
        )
        creadas += resultado.creadas
    if corregibles and rng.random() < prob_correccion:
        area, dia, estudiante, competencia = corregibles[int(rng.integers(len(corregibles)))]
        celda = {
            "estudiante": estudiante,
            "competencia": competencia,
            "nivel": "AD",
            "conclusion": "",
            "base": {"nivel": "A", "conclusion": ""},
        }
        momento = _momento(dia, HORA_CORRECCION)
        with _a_la_fecha(cuenta, momento):
            notas.guardar_hoja(
                cuenta, seccion, periodo.numero, area.codigo_siagie, [celda], hoy=dia
            )
        Calificacion.objects.filter(
            estudiante_id=estudiante, competencia_id=competencia, periodo=periodo
        ).update(actualizado_en=momento)
    return creadas


# ── sesiones ─────────────────────────────────────────────────────────────────────────────────


def _enviar_sesion(cuenta, datos, archivo):
    """El envío por el servicio; aparte para que las pruebas simulen una falla."""
    return repositorio.enviar_sesion(cuenta, datos, archivo)


def _sesiones(seccion, cuenta, docente, dias, valores, rng, escritas):
    """Poisson(``sesiones_semana``) sesiones por semana, en días de la ventana."""
    media = valores["autorregistro"]["sesiones_semana"]
    areas = list(
        InstitucionArea.objects.filter(
            institucion_id=seccion.anio_escolar.institucion_id, se_trabaja=True
        )
        .select_related("area")
        .order_by("area__orden", "area__pk")
    )
    semanas = {}
    for dia in dias:
        semanas.setdefault(dia - datetime.timedelta(days=dia.weekday()), []).append(dia)
    enviadas = 0
    for semana in sorted(semanas):
        for _ in range(int(rng.poisson(media))):
            dia = semanas[semana][int(rng.integers(len(semanas[semana])))]
            area = areas[int(rng.integers(len(areas)))].area
            enviadas += 1
            titulo = f"Sesión simulada {enviadas} de {area.nombre}"
            datos = {
                "id": str(uuid.uuid5(ESPACIO_SESIONES, f"{docente.usuario}-{enviadas}")),
                "grado": str(docente.grado),
                "area": str(area.pk),
                "titulo": titulo,
                "proposito": f"Propósito simulado de la sesión de {area.nombre}.",
            }
            contenido = docx_con_texto([ORIGEN, titulo, datos["proposito"]])
            archivo = SimpleUploadedFile(
                f"sesion-simulada-{docente.usuario}-{enviadas}.docx",
                contenido,
                content_type=TIPO_DOCX,
            )
            momento = _momento(dia, HORA_SESION)
            # El id va a la lista antes del envío: la clave del archivo lleva un token al azar y
            # el archivo puede quedar escrito aunque la carga falle justo después.
            escritas.append(datos["id"])
            with _a_la_fecha(cuenta, momento):
                sesion = _enviar_sesion(cuenta, datos, archivo)
            Sesion.objects.filter(pk=sesion.pk).update(creado_en=momento)
    return enviadas


def _borrar_escritas(ids):
    """Borra ``sesiones/<id>-<token>.<ext>`` de cada sesión de ``ids`` (carga fallida)."""
    if not ids:
        return
    almacen = storages["sesiones"]
    prefijos = tuple(f"{id_sesion}-" for id_sesion in ids)
    try:
        _, nombres = almacen.listdir("sesiones")
    except FileNotFoundError:
        return
    for nombre in nombres:
        if nombre.startswith(prefijos):
            try:
                almacen.delete(f"sesiones/{nombre}")
            except Exception:
                logger.exception(
                    "No se pudo borrar %s, de una carga de la simulación fallida.", nombre
                )


# ── cargar y quitar ──────────────────────────────────────────────────────────────────────────


def _arbol():
    return parametros.cargar()


def cargar_simulacion(clave, confirmar=False, arbol=None) -> ResumenCarga:
    """Carga la ventana O2 de la corrida principal, todo o nada.

    Se niega sin DEBUG, sin ``confirmar`` o sin clave; si la institución simulada tiene datos que
    no son de la simulación, si ya hay una carga o si alguna ``simNN`` es de otra institución.
    Si algo falla, borra los archivos de las sesiones que alcanzó a escribir.
    """
    base._exigir_local()
    _exigir_confirmar(confirmar)
    base._exigir_clave(clave)
    valores = parametros.valores(arbol if arbol is not None else _arbol())
    semilla = valores["semillas"]["principal"]
    lista = docentes_principales(valores, semilla)
    rng = _hijos(semilla)[3]
    dias = dias_de_la_ventana(valores)
    escritas = []
    try:
        return _cargar(lista, dias, valores, rng, clave, escritas)
    except BaseException:
        _borrar_escritas(escritas)
        raise


def _cargar(lista, dias, valores, rng, clave, escritas):
    resumen = ResumenCarga()
    with transaction.atomic():
        institucion = base.preparar_base()
        base._revisar_ajenos(institucion)
        _revisar_cuentas(institucion, [d.usuario for d in lista])
        _revisar_vacia(institucion)
        for docente in lista:
            cuenta = _cuenta(institucion, docente, clave)
            seccion = _seccion(institucion, docente, cuenta, dias[-1])
            resumen.docentes += 1
            resumen.estudiantes += docente.n_estudiantes
            resumen.jornadas += _asistencia(seccion, cuenta, docente, dias, valores, rng)
            resumen.notas += _notas(seccion, cuenta, dias, valores, rng)
            resumen.sesiones += _sesiones(seccion, cuenta, docente, dias, valores, rng, escritas)
    return resumen


TABLAS_DE_LA_CARGA = (
    Estudiante,
    Jornada,
    Asistencia,
    Calificacion,
    CompetenciaPeriodo,
    Sesion,
    RegistroActividad,
)


def _analizar():
    """``ANALYZE`` de las tablas de la carga antes de borrar.

    Sin estadísticas al día, el ``DELETE … WHERE id IN (SELECT … JOIN …)`` de
    ``demo.descartar_seccion`` tardaba minutos por sección sobre tablas recién llenadas.
    """
    with connection.cursor() as cursor:
        for modelo in TABLAS_DE_LA_CARGA:
            cursor.execute(f"ANALYZE {connection.ops.quote_name(modelo._meta.db_table)}")


def quitar_simulacion(confirmar=False) -> ResumenQuitar:
    """Limpia la carga (con ``preparar_rutas.quitar``) y el registro de actividad de las simNN.

    Borra también las entradas que dejaron los agentes de G2. ``QuerySet.delete()`` no pasa por
    el ``delete`` de solo lectura del modelo. Solo las cuentas de la institución simulada.
    """
    base._exigir_local()
    _exigir_confirmar(confirmar)
    institucion = base._institucion()
    if institucion is None:
        return ResumenQuitar()
    with transaction.atomic():
        _analizar()
        estudiantes = base.quitar()
        entradas, _ = RegistroActividad.objects.filter(
            usuario__institucion=institucion, usuario__username__regex=r"^sim\d{2}$"
        ).delete()
    return ResumenQuitar(estudiantes=estudiantes, entradas=entradas)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"Carga de la simulación ({ORIGEN.lower()}).")
    parser.add_argument("orden", choices=["cargar", "quitar"])
    parser.add_argument("--confirmar", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.orden == "cargar":
            resumen = cargar_simulacion(
                os.environ.get("SIM_CLAVE", ""), confirmar=args.confirmar, arbol=_arbol()
            )
            print(resumen.texto)
        else:
            resumen = quitar_simulacion(confirmar=args.confirmar)
            print(
                f"{ORIGEN}: {resumen.estudiantes} estudiantes y {resumen.entradas} entradas del "
                "registro borrados. La base queda armada."
            )
    except (base.BaseNoSegura, ValidationError) as error:
        print(" ".join(getattr(error, "messages", [str(error)])))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
