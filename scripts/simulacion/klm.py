"""Rutas de los agentes y su conversión a operadores KLM (G2). Datos simulados.

Los tiempos de O2 salen de operadores KLM (``o2.operadores_klm``, SUPUESTO sin ancla), nunca del
reloj del agente: una ruta con segundos, duración o marcas de tiempo se rechaza. El script decide
qué hace la docente; el agente decide cómo usa la interfaz y deja su ruta.

El KLM cubre solo la ruta ideal que el agente ejecutó. Los pasos marcados ``desvio: true`` y las
``confusiones`` quedan registrados como hallazgos de usabilidad, pero no entran al cálculo; el
recargo por no ser experto lo aplica ``medicion.py`` una sola vez (``factor_no_experto_*``).

Reglas para colocar M (adaptación de la práctica común de KLM; fuente original pendiente):
  1. Una M al iniciar cada subtarea (paso con ``inicia_subtarea``).
  2. Una M antes de una decisión entre opciones visibles (``decision``).
  3. Una M al verificar un aviso o confirmación del sistema (``verifica``).
  4. Un paso lleva a lo más una M, aunque tenga varias marcas.
  5. Sin M en la secuencia repetida por estudiante (``por_estudiante``) ni por excepción
     (``por_excepcion``): va agrupada.

Un paso ``por_estudiante`` se repite con cada estudiante. Un paso ``por_excepcion`` se repite solo
con los estudiantes que no marcan «Asistió» (marcado masivo y luego corregir a quienes faltaron):
suma a ``por_estudiante`` multiplicado por ``poblacion.tasa_excepciones_asistencia``, el mismo
parámetro que usa la simulación para O1.

Un paso ``por_conclusion`` se repite solo con los estudiantes cuyo nivel es B o C, que llevan
conclusión descriptiva (spec registro-notas, RN-003): suma a ``por_estudiante`` multiplicado por
``poblacion.proporcion_conclusion_notas``. La acción ``texto`` equivale a una tecla por carácter
(``poblacion.caracteres_conclusion``) en un paso ``por_conclusion``. Fuera de la conclusión, «texto»
lleva ``caracteres: N``: el largo del texto fijo de la consigna (título, propósito), N teclas.
"""

from pathlib import Path

import yaml

from simulacion.medicion import PERSONAS, TAREAS_KLM

CARPETA_RUTAS = Path(__file__).with_name("rutas")
ARCHIVO_TABLA = Path(__file__).with_name("klm") / "tabla.yaml"

# Acción registrada por el agente → operadores KLM (M y R se tratan aparte, R por contexto).
ACCIONES = {
    "tecla": ("K",),
    "apuntar": ("P",),
    "clic": ("B",),
    "tap": ("P", "B"),
    "manos": ("H",),
    "espera": ("R",),
    "texto": ("T",),  # una tecla por carácter de la conclusión
    "lectura": (),  # leer un aviso o un diálogo: solo la M de ``verifica``, sin operador propio
}
MARCAS_M = ("inicia_subtarea", "decision", "verifica")
FIJO, POR_ESTUDIANTE, POR_EXCEPCION = "fijo", "por_estudiante", "por_excepcion"
POR_CONCLUSION = "por_conclusion"
AMBITOS = (POR_ESTUDIANTE, POR_EXCEPCION, POR_CONCLUSION)
CAMPOS_DE_RELOJ = ("segundos", "duracion", "tiempo", "ms", "reloj", "minutos", "timestamp")
CAMPOS_OBLIGATORIOS = ("persona", "tarea", "exito", "errores", "confusiones", "pasos")
# Tarea → contexto de o2.contexto_tarea (el dispositivo y la conexión los fija la tarea).
CONTEXTO_DE_TAREA = {
    "sesion_entrega": "sesion",
    "notas": "notas",
    "corregir_nota": "notas",
    "asistencia_momento": "asistencia",
    "asistencia_diferido": "asistencia",
}
CLAVE_R = {"domestica": "R_domestica", "Slow 4G": "R_slow_4g"}


class RutaInvalida(ValueError):
    """Una ruta no sigue el formato (o trae tiempos del reloj)."""


def _validar_texto(i: int, paso: dict) -> None:
    """«texto» es la conclusión (caracteres del parámetro) o un texto fijo de la consigna."""
    if paso["accion"] != "texto":
        if "caracteres" in paso:
            raise RutaInvalida(f"Paso {i}: «caracteres» solo vale en la acción texto.")
        return
    if paso.get("por_conclusion"):
        if "caracteres" in paso:
            raise RutaInvalida(
                f"Paso {i}: los caracteres de la conclusión salen del parámetro, no de la ruta "
                "(quita «caracteres»)."
            )
        return
    caracteres = paso.get("caracteres")
    if caracteres is None:
        raise RutaInvalida(
            f"Paso {i}: «texto» vale en un paso por_conclusion o con «caracteres» (texto fijo)."
        )
    if not (isinstance(caracteres, int) and not isinstance(caracteres, bool) and caracteres > 0):
        raise RutaInvalida(f"Paso {i}: «caracteres» debe ser un entero positivo.")
    if any(paso.get(a) for a in AMBITOS):
        raise RutaInvalida(f"Paso {i}: un texto fijo de la consigna va en el ámbito fijo.")


def validar_ruta(ruta: dict) -> None:
    for campo in CAMPOS_DE_RELOJ:
        if campo in ruta:
            raise RutaInvalida(f"La ruta trae «{campo}»: los tiempos salen de KLM, no del reloj.")
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in ruta:
            raise RutaInvalida(f"Falta el campo «{campo}» en la ruta.")
    if ruta["persona"] not in PERSONAS:
        raise RutaInvalida(f"persona desconocida: {ruta['persona']!r}.")
    if ruta["tarea"] not in TAREAS_KLM:
        raise RutaInvalida(f"tarea desconocida: {ruta['tarea']!r}.")
    if not ruta["pasos"]:
        raise RutaInvalida("La ruta no tiene pasos.")
    for i, paso in enumerate(ruta["pasos"], start=1):
        for campo in CAMPOS_DE_RELOJ:
            if campo in paso:
                raise RutaInvalida(f"Paso {i}: trae «{campo}»; los tiempos salen de KLM.")
        if paso.get("accion") not in ACCIONES:
            raise RutaInvalida(f"Paso {i}: accion desconocida {paso.get('accion')!r}.")
        if not paso.get("objetivo"):
            raise RutaInvalida(f"Paso {i}: sin objetivo.")
        if sum(bool(paso.get(a)) for a in AMBITOS) > 1:
            raise RutaInvalida(
                f"Paso {i}: solo uno entre por_estudiante, por_excepcion y por_conclusion."
            )
        _validar_texto(i, paso)


def _ambito(paso: dict) -> str:
    return next((a for a in AMBITOS if paso.get(a)), FIJO)


def operadores_de(ruta: dict) -> list[tuple[str, str]]:
    """Operadores de la ruta ideal: ``(operador, ámbito)`` en orden.

    El ámbito es ``fijo``, ``por_estudiante``, ``por_excepcion`` o ``por_conclusion``.
    """
    validar_ruta(ruta)
    salida = []
    for paso in ruta["pasos"]:
        if paso.get("desvio"):
            continue
        ambito = _ambito(paso)
        if ambito == FIJO and any(paso.get(marca) for marca in MARCAS_M):
            salida.append(("M", FIJO))
        if paso["accion"] == "texto" and ambito == FIJO:
            salida += [("K", FIJO)] * paso["caracteres"]
        else:
            salida += [(op, ambito) for op in ACCIONES[paso["accion"]]]
    return salida


def _segundos(valores: dict, tarea: str) -> dict:
    o2 = valores["o2"]
    contexto = o2["contexto_tarea"][CONTEXTO_DE_TAREA[tarea]]
    ops = o2["operadores_klm"]
    segundos = {op: ops[op] for op in ("K", "P", "B", "H", "M")}
    segundos["R"] = ops[CLAVE_R[contexto["conexion"]]]
    segundos["T"] = ops["K"]
    return segundos


def tiempo_ruta(ruta: dict, valores: dict) -> dict:
    """``{fijo, por_estudiante}`` en minutos, con los operadores y el contexto de la tarea."""
    segundos = _segundos(valores, ruta["tarea"])
    poblacion = valores["poblacion"]
    peso = {
        POR_ESTUDIANTE: 1.0,
        POR_EXCEPCION: poblacion["tasa_excepciones_asistencia"],
        POR_CONCLUSION: poblacion["proporcion_conclusion_notas"],
    }
    celda = {"fijo": 0.0, "por_estudiante": 0.0}
    for operador, ambito in operadores_de(ruta):
        minutos = segundos[operador] / 60
        if operador == "T":
            minutos *= poblacion["caracteres_conclusion"]
        if ambito == FIJO:
            celda["fijo"] += minutos
        else:
            celda["por_estudiante"] += minutos * peso[ambito]
    return celda


def construir_tabla(rutas: list[dict], valores: dict) -> dict:
    """``tabla[persona][tarea] = {fijo, por_estudiante}``; una ruta por celda."""
    tabla: dict = {}
    for ruta in rutas:
        celda = tiempo_ruta(ruta, valores)
        persona, tarea = ruta["persona"], ruta["tarea"]
        if tarea in tabla.get(persona, {}):
            raise RutaInvalida(f"Ruta repetida: {persona} · {tarea}.")
        tabla.setdefault(persona, {})[tarea] = celda
    return tabla


def hallazgos(rutas: list[dict]) -> list[dict]:
    """Éxito, errores y confusiones de las rutas con alguna novedad (usabilidad, no tiempo)."""
    filas = [
        {
            "persona": r["persona"],
            "tarea": r["tarea"],
            "confusiones": len(r["confusiones"]),
            "errores": len(r["errores"]),
            "exito": r["exito"],
        }
        for r in rutas
    ]
    return [f for f in filas if f["confusiones"] or f["errores"] or not f["exito"]]


def cargar_rutas(carpeta: Path = CARPETA_RUTAS) -> list[dict]:
    rutas = []
    for archivo in sorted(Path(carpeta).glob("*.yaml")):
        ruta = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        try:
            validar_ruta(ruta)
        except RutaInvalida as error:
            raise RutaInvalida(f"{archivo.name}: {error}") from error
        rutas.append(ruta)
    return rutas


def guardar_tabla(tabla: dict, archivo: Path = ARCHIVO_TABLA) -> None:
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(yaml.safe_dump(tabla, allow_unicode=True, sort_keys=True), encoding="utf-8")


def cargar_tabla(archivo: Path = ARCHIVO_TABLA) -> dict:
    return yaml.safe_load(archivo.read_text(encoding="utf-8"))


def generar_tabla(
    valores: dict, carpeta: Path = CARPETA_RUTAS, destino: Path = ARCHIVO_TABLA
) -> dict:
    """Arma la tabla con las rutas de ``carpeta`` y los operadores de ``valores``, y la guarda."""
    tabla = construir_tabla(cargar_rutas(carpeta), valores)
    guardar_tabla(tabla, destino)
    return tabla


if __name__ == "__main__":
    from simulacion import parametros

    generar_tabla(parametros.valores(parametros.cargar()))
    print(f"Tabla KLM guardada en {ARCHIVO_TABLA}")
