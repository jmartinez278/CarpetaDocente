"""Reglas de negocio del módulo institucion (documento 12: capa de servicios)."""

import unicodedata
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.db.models import Count, ProtectedError, Q, RestrictedError
from django.utils import timezone

from actividad.models import Operacion
from actividad.servicios import registrar
from cuentas.models import Usuario
from institucion.models import (
    MENSAJE_CRUCE,
    AnioEscolar,
    Estudiante,
    Institucion,
    Periodo,
    Seccion,
)

SECCION_OCUPADA = "La sección ya tiene un docente asignado"
SIN_SECCION = "Tu sección aparecerá cuando el administrador la asigne."
GRADOS = range(1, 7)
NOMBRES_SECCION = ("A", "B", "C", "D")
DOCENTE_NO_ELEGIBLE = "Elige una docente activa de la institución del año escolar."
MAX_ESTUDIANTES_LISTA = 60


def normalizar_nombre(texto):
    """Apellidos o nombres en mayúsculas y sin espacios de más (US-006, D1).

    ``split()`` también quita los espacios duros (U+00A0) que trae Excel; ``upper()``
    conserva tildes y Ñ.
    """
    return unicodedata.normalize("NFC", " ".join(texto.split()).upper())


@dataclass(frozen=True)
class ErrorLista:
    """Error de la lista pegada: las líneas afectadas, su motivo y cómo corregirlo (D3)."""

    lineas: tuple
    motivo: str
    ayuda: str

    @property
    def titulo(self):
        """ "Línea 7: motivo", "Líneas 4 y 12: motivo" o el motivo solo (sin líneas)."""
        if not self.lineas:
            return self.motivo
        if len(self.lineas) == 1:
            return f"Línea {self.lineas[0]}: {self.motivo}"
        *primeras, ultima = self.lineas
        return f"Líneas {', '.join(map(str, primeras))} y {ultima}: {self.motivo}"


def _error_de_formato(linea):
    """Motivo y ayuda de una línea con texto mal formada, o ``None`` si está bien (D3, 4)."""
    if "\t" in linea:
        return (
            "pega solo la columna de apellidos y nombres",
            "Quita las demás columnas de esa línea.",
        )
    comas = linea.count(",")
    if comas == 0:
        return (
            "falta la coma entre apellidos y nombres",
            "Separa los apellidos de los nombres con una coma.",
        )
    if comas > 1:
        return "tiene más de una coma", "Deja una sola coma, entre apellidos y nombres."
    apellidos, nombres = (normalizar_nombre(lado) for lado in linea.split(","))
    ayuda = "Escribe apellidos y nombres separados por una coma."
    if not apellidos:
        return "faltan los apellidos", ayuda
    if not nombres:
        return "faltan los nombres", ayuda
    return None


def leer_lista_pegada(texto):
    """Lee el texto pegado: devuelve ``(filas, errores)`` sin tocar la base de datos (D3).

    Las filas son ``(linea, apellidos, nombres)`` ya normalizadas. La línea se numera por su
    posición en el texto, contando las líneas en blanco, que se ignoran. Con más de 60 líneas
    con texto devuelve solo ese error. Una línea con error muestra un solo motivo.
    """
    # Sin ``splitlines()``: también corta en U+2028 y desfasaría la numeración.
    lineas = texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    con_texto = [(numero, linea) for numero, linea in enumerate(lineas, start=1) if linea.strip()]
    if len(con_texto) > MAX_ESTUDIANTES_LISTA:
        error = ErrorLista(
            (),
            f"La lista tiene {len(con_texto)} líneas; el máximo es {MAX_ESTUDIANTES_LISTA}",
            "Pega solo los estudiantes de tu sección.",
        )
        return [], [error]
    filas, errores = [], []
    for numero, linea in con_texto:
        problema = _error_de_formato(linea)
        if problema is None:
            apellidos, nombres = (normalizar_nombre(lado) for lado in linea.split(","))
            filas.append((numero, apellidos, nombres))
        else:
            errores.append(ErrorLista((numero,), *problema))
    return filas, errores


def texto_seccion(seccion):
    """Texto de una sección: "2.º grado, sección A", con el ordinal º (U+00BA) (US-005, D2)."""
    return f"{seccion.grado}.º grado, sección {seccion.nombre}"


def texto_seccion_corto(seccion):
    """Texto corto para el título del diálogo: "2.º A" (US-006, D2)."""
    return f"{seccion.grado}.º {seccion.nombre}"


def secciones_docente(usuario):
    """Secciones del docente en el año ABIERTO, por grado y nombre (US-006, D2)."""
    return Seccion.objects.filter(
        docente=usuario, anio_escolar__estado=AnioEscolar.Estado.ABIERTO
    ).order_by("grado", "nombre")


def seccion_unica(usuario):
    """La sección del año ABIERTO si el docente tiene exactamente una, con su cantidad.

    La cantidad de estudiantes va en ``cantidad_estudiantes``. Con varias secciones o con
    ninguna devuelve ``None``: la portada no ofrece entrada a la lista (US-006, D2).
    """
    secciones = list(
        secciones_docente(usuario).annotate(cantidad_estudiantes=Count("estudiantes"))[:2]
    )
    return secciones[0] if len(secciones) == 1 else None


def texto_secciones_docente(usuario):
    """Línea de la portada con las secciones del docente en el año ABIERTO (US-005, D2).

    Van ordenadas por grado y nombre y unidas con " · ". Sin ninguna, avisa que aparecerá.
    """
    secciones = secciones_docente(usuario)
    if not secciones:
        return SIN_SECCION
    return " · ".join(texto_seccion(seccion) for seccion in secciones)


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
      Docente de la institución del año escolar, según la base de datos y no según el objeto.

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
    # La cuenta se relee: ``seccion.docente`` puede ser una copia vieja (activa, con otro rol
    # o de otra institución cuando ya no lo es en la base).
    elegible = Usuario.objects.filter(
        pk=seccion.docente_id,
        rol=Usuario.Rol.DOCENTE,
        is_active=True,
        institucion_id=seccion.anio_escolar.institucion_id,
    ).exists()
    if not elegible:
        raise ValidationError({"docente": DOCENTE_NO_ELEGIBLE})


def cargar_secciones(institucion, anio):
    """Crea el año ABIERTO y sus secciones de 1.º a 6.º, A a D, sin docentes (US-005, D2).

    Es idempotente. Devuelve ``(anio_escolar, anio_creado, secciones_creadas)``. Si el año
    ya existe CERRADO, o la institución tiene otro año ABIERTO, lanza ``ValidationError``
    y no crea nada. Lo corre un comando de consola: ANIO_CREADO y cada SECCION_CREADA
    quedan con el usuario vacío (US-008).
    """
    with transaction.atomic():
        existente = AnioEscolar.objects.filter(institucion=institucion, anio=anio).first()
        if existente is not None and existente.estado == AnioEscolar.Estado.CERRADO:
            raise ValidationError(f"El año {anio} está cerrado: no se cargan secciones en él.")
        otro_abierto = (
            AnioEscolar.objects.filter(institucion=institucion, estado=AnioEscolar.Estado.ABIERTO)
            .exclude(anio=anio)
            .first()
        )
        if otro_abierto is not None:
            raise ValidationError(
                f"La institución ya tiene el año {otro_abierto.anio} abierto: "
                f"ciérralo antes de cargar el {anio}."
            )
        anio_escolar, anio_creado = AnioEscolar.objects.get_or_create(
            institucion=institucion, anio=anio, defaults={"estado": AnioEscolar.Estado.ABIERTO}
        )
        if anio_creado:
            registrar(None, Operacion.ANIO_CREADO, entidad="anio_escolar", entidad_id=anio_escolar)
        secciones_creadas = 0
        for grado in GRADOS:
            for nombre in NOMBRES_SECCION:
                seccion, creada = Seccion.objects.get_or_create(
                    anio_escolar=anio_escolar, grado=grado, nombre=nombre
                )
                if creada:
                    registrar(None, Operacion.SECCION_CREADA, entidad="seccion", entidad_id=seccion)
                secciones_creadas += creada
    return anio_escolar, anio_creado, secciones_creadas


# --- Lista de estudiantes de una sección (US-006, D2) ---

ESTUDIANTE_REPETIDO = "Este estudiante ya está en la lista"
MAX_CARACTERES_NOMBRE = 120
AYUDA_REPETIDO = (
    "Deja una sola línea. Si son personas distintas, escribe el segundo nombre completo."
)


class SeccionConEstudiantes(Exception):
    """Pegar lista solo se usa con la sección vacía."""


class ListaConRegistros(Exception):
    """Un estudiante afectado tiene registros (asistencia o notas): no se borra ninguno."""


def _clave_orden(texto):
    """Letra a letra, sin tildes y con la Ñ entre la N y la O (alfabeto español)."""
    clave = []
    for letra in texto:
        if letra == "Ñ":
            clave.append(2 * ord("N") + 1)
        else:
            clave.append(2 * ord(unicodedata.normalize("NFD", letra)[0]))
    return clave


def estudiantes_ordenados(seccion):
    """Estudiantes por apellidos y nombres, ordenados en Python (D2).

    No depende de la *collation* de PostgreSQL, que en local y en Neon puede poner "Á"
    después de "Z". Con 60 estudiantes como máximo no cuesta nada.
    """
    return sorted(
        seccion.estudiantes.all(),
        key=lambda e: (
            _clave_orden(e.apellidos),
            _clave_orden(e.nombres),
            e.apellidos,
            e.nombres,
        ),
    )


def _errores_de_filas(filas):
    """Errores de las filas bien formadas: más de 120 caracteres y repetidos (D3, 5)."""
    errores = []
    validas = []
    for linea, apellidos, nombres in filas:
        campo = (
            "apellidos"
            if len(apellidos) > MAX_CARACTERES_NOMBRE
            else "nombres"
            if len(nombres) > MAX_CARACTERES_NOMBRE
            else None
        )
        if campo is None:
            validas.append((linea, apellidos, nombres))
        else:
            errores.append(
                ErrorLista(
                    (linea,),
                    f"los {campo} tienen más de {MAX_CARACTERES_NOMBRE} caracteres",
                    f"Usa un máximo de {MAX_CARACTERES_NOMBRE} caracteres por campo, "
                    "sin datos adicionales.",
                )
            )
    por_estudiante = {}
    for linea, apellidos, nombres in validas:
        por_estudiante.setdefault((apellidos, nombres), []).append(linea)
    errores.extend(
        ErrorLista(tuple(lineas), "el mismo estudiante", AYUDA_REPETIDO)
        for lineas in por_estudiante.values()
        if len(lineas) > 1
    )
    return errores


def importar_lista(seccion, texto, usuario=None):
    """Importa el texto pegado a una sección vacía y deja ESTUDIANTES_IMPORTADOS (US-008).

    Las reglas son las de ``importar_lista_sin_registro``; con errores no queda entrada.
    """
    with transaction.atomic():
        cantidad, errores = importar_lista_sin_registro(seccion, texto)
        if cantidad:
            registrar(
                usuario,
                Operacion.ESTUDIANTES_IMPORTADOS,
                entidad="seccion",
                entidad_id=seccion,
                detalle={"cantidad": cantidad},
            )
    return cantidad, errores


def importar_lista_sin_registro(seccion, texto):
    """Importa el texto pegado a una sección vacía, todo o nada (D2).

    Sin entrada de actividad: solo la usa ``demo.cargar_demo``, que se registra entera como
    DEMO_CARGADA (US-008).

    Devuelve ``(cantidad, errores)``: con errores no guarda nada y la cantidad es 0. Si la
    sección ya tiene estudiantes lanza ``SeccionConEstudiantes`` sin leer el texto; la
    comprobación va bajo el bloqueo de la fila de la sección, así dos pestañas que importan
    a la vez no suman dos listas. ``bulk_create`` no llama a ``save()``: las filas ya vienen
    normalizadas de ``leer_lista_pegada``.
    """
    with transaction.atomic():
        Seccion.objects.select_for_update().get(pk=seccion.pk)
        if seccion.estudiantes.exists():
            raise SeccionConEstudiantes
        filas, errores = leer_lista_pegada(texto)
        if not filas and not errores:
            return 0, [
                ErrorLista(
                    (),
                    "Pega al menos un estudiante",
                    "Copia la columna de apellidos y nombres de tu Excel y pégala aquí",
                )
            ]
        errores = sorted(
            [*errores, *_errores_de_filas(filas)],
            key=lambda error: error.lineas[0] if error.lineas else 0,
        )
        if errores:
            return 0, errores
        Estudiante.objects.bulk_create(
            Estudiante(seccion=seccion, apellidos=apellidos, nombres=nombres)
            for _, apellidos, nombres in filas
        )
    return len(filas), []


def _guardar_estudiante(estudiante, existente=False):
    """Valida (campos y ``uq_estudiante``) y guarda; un homónimo por carrera da el mismo error.

    Con ``existente`` solo actualiza: si otra petición lo quitó entretanto, el ``save()`` normal
    lo volvería a crear con la misma PK; aquí lanza ``Estudiante.DoesNotExist``.
    """
    estudiante.full_clean()
    try:
        with transaction.atomic():
            estudiante.save(force_update=existente)
    except IntegrityError:
        raise ValidationError(ESTUDIANTE_REPETIDO) from None
    except DatabaseError:
        raise Estudiante.DoesNotExist from None
    return estudiante


def agregar_estudiante(seccion, apellidos, nombres, usuario=None):
    """Agrega un estudiante normalizado a la sección; ``ValidationError`` si no es válido.

    Deja ESTUDIANTE_AGREGADO en la misma transacción (US-008).
    """
    estudiante = Estudiante(
        seccion=seccion,
        apellidos=normalizar_nombre(apellidos),
        nombres=normalizar_nombre(nombres),
    )
    with transaction.atomic():
        _guardar_estudiante(estudiante)
        registrar(
            usuario, Operacion.ESTUDIANTE_AGREGADO, entidad="estudiante", entidad_id=estudiante
        )
    return estudiante


def editar_estudiante(estudiante, apellidos, nombres, usuario=None):
    """Corrige apellidos y nombres con las reglas de ``agregar_estudiante``.

    Si el estudiante ya no existe (quitado en otra pestaña), lanza ``Estudiante.DoesNotExist``.
    Deja ESTUDIANTE_EDITADO con los campos que cambiaron, nunca los nombres (US-008, RN-015);
    sin cambios, no deja entrada. Compara con la fila guardada y bloqueada, no con ``estudiante``:
    una copia vieja que revierte otra edición también es un cambio (RNF-016).
    """
    nuevos = {"apellidos": normalizar_nombre(apellidos), "nombres": normalizar_nombre(nombres)}
    estudiante.apellidos = nuevos["apellidos"]
    estudiante.nombres = nuevos["nombres"]
    with transaction.atomic():
        guardado = (
            Estudiante.objects.select_for_update().filter(pk=estudiante.pk).values(*nuevos).first()
        )
        if guardado is None:
            raise Estudiante.DoesNotExist
        campos = [campo for campo, valor in nuevos.items() if guardado[campo] != valor]
        _guardar_estudiante(estudiante, existente=True)
        if campos:
            registrar(
                usuario,
                Operacion.ESTUDIANTE_EDITADO,
                entidad="estudiante",
                entidad_id=estudiante,
                detalle={"campos": campos},
            )
    return estudiante


def quitar_estudiante(estudiante, usuario=None):
    """Borra al estudiante; con registros que lo referencian lanza ``ListaConRegistros``.

    La regla no consulta tablas: la dan las FK ``RESTRICT`` (hoy, ``asistencia``). Deja
    ESTUDIANTE_QUITADO en la misma transacción (US-008).
    """
    estudiante_id = estudiante.pk
    try:
        with transaction.atomic():
            estudiante.delete()
            registrar(
                usuario,
                Operacion.ESTUDIANTE_QUITADO,
                entidad="estudiante",
                entidad_id=estudiante_id,
            )
    except (RestrictedError, ProtectedError):
        raise ListaConRegistros from None


def vaciar_lista(seccion, usuario=None):
    """Borra a todos los estudiantes de la sección o a ninguno (``ListaConRegistros``).

    Deja LISTA_VACIADA con la cantidad borrada, en la misma transacción (US-008).
    """
    try:
        with transaction.atomic():
            _, borrados = seccion.estudiantes.all().delete()
            cantidad = borrados.get(Estudiante._meta.label, 0)
            if cantidad:  # una lista ya vacía no cambia nada
                registrar(
                    usuario,
                    Operacion.LISTA_VACIADA,
                    entidad="seccion",
                    entidad_id=seccion,
                    detalle={"cantidad": cantidad},
                )
    except (RestrictedError, ProtectedError):
        raise ListaConRegistros from None


# --- Periodos del año escolar (US-028, D2, D4, D6 y D8) ---

PERIODOS_POR_ORGANIZACION = {
    Institucion.OrganizacionPeriodos.BIMESTRE: 4,
    Institucion.OrganizacionPeriodos.TRIMESTRE: 3,
}
ANIO_CERRADO = "El año escolar está cerrado: sus periodos no cambian."
SIN_ORGANIZACION = (
    "Define la organización de periodos de la institución antes de configurar sus periodos."
)
ORGANIZACION_FIJA = (
    "La organización de periodos ya no cambia: la institución tiene periodos guardados."
)
FIN_ANTES_DEL_INICIO = "La fecha de fin debe ser posterior a la de inicio."
# MENSAJE_CRUCE viene de ``models``: también lo usa la restricción de la base.


def mensaje_incompletas(cantidad):
    return f"Completa las fechas de los {cantidad} periodos."


def mensaje_fuera_del_anio(anio):
    return f"Las fechas deben estar dentro de {anio}."


def mensaje_orden(numero):
    """Para el periodo ``numero`` que empieza antes de que termine el anterior."""
    return f"El periodo {numero} debe empezar después de que termina el periodo {numero - 1}."


@dataclass(frozen=True)
class CambiosPeriodos:
    """Lo que dejó ``guardar_periodos``: los periodos creados y el detalle de cada editado."""

    creados: list
    editados: list


def validar_periodos(anio, filas):
    """Valida las filas nuevas ``(numero, inicio, fin)`` de un año, todas juntas (D2).

    Usa ``anio.estado`` y la organización de ``anio.institucion`` tal como vienen: quien guarda
    los pasa releídos y bloqueados. Los errores de una fila van en un diccionario por número
    (``message_dict``); los del conjunto, sin número. En este orden: año CERRADO, organización
    vacía, filas incompletas, fechas de cada fila, cruce (en la fila de número mayor) y orden.
    Todas las filas vacías es válido si el año aún no tiene periodos (nada que guardar).
    """
    if anio.estado == AnioEscolar.Estado.CERRADO:
        raise ValidationError(ANIO_CERRADO)
    cantidad = PERIODOS_POR_ORGANIZACION.get(anio.institucion.organizacion_periodos)
    if cantidad is None:
        raise ValidationError(SIN_ORGANIZACION)
    por_numero = {numero: (inicio, fin) for numero, inicio, fin in filas}
    if set(por_numero) - set(range(1, cantidad + 1)):
        raise ValueError(f"Las filas deben ir numeradas de 1 a {cantidad}.")
    fechas = [por_numero.get(numero, (None, None)) for numero in range(1, cantidad + 1)]
    vacias = all(inicio is None and fin is None for inicio, fin in fechas)
    if vacias and not anio.periodos.exists():
        return
    if any(inicio is None or fin is None for inicio, fin in fechas):
        raise ValidationError(mensaje_incompletas(cantidad))

    errores = {}
    for numero, (inicio, fin) in enumerate(fechas, start=1):
        if fin <= inicio:
            errores[numero] = FIN_ANTES_DEL_INICIO
        elif inicio.year != anio.anio or fin.year != anio.anio:
            errores[numero] = mensaje_fuera_del_anio(anio.anio)
    if errores:
        raise ValidationError(errores)

    # Con los bordes incluidos: se cruzan si cada uno empieza a más tardar el día en que el
    # otro termina.
    for numero in range(2, cantidad + 1):
        inicio, fin = fechas[numero - 1]
        if any(
            inicio <= otro_fin and otro_inicio <= fin
            for otro_inicio, otro_fin in fechas[: numero - 1]
        ):
            errores[numero] = MENSAJE_CRUCE
    if errores:
        raise ValidationError(errores)

    for numero in range(2, cantidad + 1):
        if fechas[numero - 1][0] <= fechas[numero - 2][1]:
            errores[numero] = mensaje_orden(numero)
    if errores:
        raise ValidationError(errores)


def guardar_periodos(anio, filas, usuario=None):
    """Única escritura de periodos: crea o corrige las N filas de un año, todas o ninguna (D4).

    Bloquea la institución y el año (en ese orden) y valida con lo releído: dos guardados del
    mismo año van en fila, y el segundo edita lo que dejó el primero. Crea o actualiza por
    número, sin borrar y sin cambiar el id de un periodo. Al final comprueba ``ex_periodo_cruce``
    (diferida, D3): un cruce que solo ve la base da ``ValidationError(MENSAJE_CRUCE)``. Deja
    PERIODOS_CONFIGURADOS si el año pasa de cero periodos a N y un PERIODO_EDITADO por periodo
    cambiado (D6). Devuelve ``CambiosPeriodos``.
    """
    with transaction.atomic():
        institucion = Institucion.objects.select_for_update().get(pk=anio.institucion_id)
        anio = AnioEscolar.objects.select_for_update().get(pk=anio.pk)
        anio.institucion = institucion
        validar_periodos(anio, filas)
        guardados = {periodo.numero: periodo for periodo in anio.periodos.select_for_update()}
        creados, editados = [], []
        for numero, inicio, fin in sorted(filas, key=lambda fila: fila[0]):
            if inicio is None:
                continue  # todas vacías y el año sin periodos: nada que guardar
            periodo = guardados.get(numero)
            if periodo is None:
                creados.append(
                    Periodo.objects.create(
                        anio_escolar=anio, numero=numero, fecha_inicio=inicio, fecha_fin=fin
                    )
                )
            elif (periodo.fecha_inicio, periodo.fecha_fin) != (inicio, fin):
                editados.append(
                    {
                        "numero": numero,
                        "inicio_antes": periodo.fecha_inicio.isoformat(),
                        "fin_antes": periodo.fecha_fin.isoformat(),
                        "inicio_despues": inicio.isoformat(),
                        "fin_despues": fin.isoformat(),
                    }
                )
                periodo.fecha_inicio, periodo.fecha_fin = inicio, fin
                periodo.save(update_fields=["fecha_inicio", "fecha_fin"])
        _comprobar_cruce()
        if creados and not guardados:
            registrar(
                usuario,
                Operacion.PERIODOS_CONFIGURADOS,
                entidad="anio_escolar",
                entidad_id=anio,
                detalle={"periodos": len(creados)},
            )
        for detalle in editados:
            registrar(
                usuario,
                Operacion.PERIODO_EDITADO,
                entidad="periodo",
                entidad_id=guardados[detalle["numero"]],
                detalle=detalle,
            )
    return CambiosPeriodos(creados, editados)


def _comprobar_cruce():
    """Adelanta la comprobación de ``ex_periodo_cruce`` y la vuelve a diferir (D3).

    En un punto de guardado: si falla, el error sale aquí y no en el ``COMMIT``. Solo el
    ``IntegrityError`` de esa restricción se traduce.
    """
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ex_periodo_cruce IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ex_periodo_cruce DEFERRED")
    except IntegrityError as error:
        restriccion = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
        if restriccion != "ex_periodo_cruce":
            raise
        raise ValidationError(MENSAJE_CRUCE) from None


def validar_organizacion(institucion):
    """La organización de periodos no cambia si algún año de la institución tiene periodos (D5).

    Compara ``institucion`` con la fila guardada. Quien guarda la tiene bloqueada (el panel la
    relee con ``FOR UPDATE``), así no se cruza con un ``guardar_periodos`` del mismo momento.
    """
    if institucion.pk is None:
        return
    guardada = (
        Institucion.objects.filter(pk=institucion.pk)
        .values_list("organizacion_periodos", flat=True)
        .first()
    )
    cambia = guardada != institucion.organizacion_periodos
    if cambia and Periodo.objects.filter(anio_escolar__institucion_id=institucion.pk).exists():
        raise ValidationError({"organizacion_periodos": ORGANIZACION_FIJA})


def periodo_vigente(origen, fecha=None):
    """El periodo que contiene ``fecha`` (bordes incluidos), o ``None`` si no hay (D8).

    ``origen`` es una ``Seccion`` o un ``AnioEscolar``; sin ``fecha``, hoy en hora de Lima. Una
    consulta. Es la única forma de obtener el periodo de una fecha (US-020 la usa).
    """
    anio_id = origen.anio_escolar_id if isinstance(origen, Seccion) else origen.pk
    fecha = fecha or timezone.localdate()
    return Periodo.objects.filter(
        anio_escolar_id=anio_id, fecha_inicio__lte=fecha, fecha_fin__gte=fecha
    ).first()
