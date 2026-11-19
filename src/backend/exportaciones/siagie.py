"""El libro «Periodo por Excel» del SIAGIE: abrir, leer y escribir (US-024/025, design D1, D2, D9).

Sin base de datos: ``servicios`` decide qué reconocer y qué escribir. Solo se escriben valores en
celdas que ya existen; no se crean hojas, estilos ni validaciones (D8). Ningún mensaje de
excepción ni registro lleva celdas del libro (RN-015): todo fallo al abrir o leer es
``PlantillaNoReconocida`` con su mensaje fijo.
"""

import io
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field

from defusedxml import ElementTree
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell

NO_ES_LA_PLANTILLA = "El archivo no corresponde a la plantilla de notas del SIAGIE"
DEMASIADO_GRANDE = "El archivo supera los 3 MB. Elige uno más pequeño."

# D9: 3 MB porque el libro vuelve en base64 (×4/3, ~4,2 MB) y una respuesta de Vercel admite
# 4,5 MB; la completada tiene el mismo tope (``servicios.completar_plantilla``). Lo descomprimido
# y la cantidad de partes se revisan antes de abrir el libro.
LIMITE_BYTES = 3 * 1024 * 1024
LIMITE_DESCOMPRIMIDO = 40 * 1024 * 1024
LIMITE_PARTES = 300
FILAS_MAXIMAS = 60
PRIMERA_FILA = 3

XLSX_MAIN = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
TIPOS_DE_CONTENIDO = "{http://schemas.openxmlformats.org/package/2006/content-types}"

HOJAS_FIJAS = {"Generalidades", "Parametros"}
HOJA_DE_AREA = re.compile(r"^(\d{3,4})-")
NUMERO_COMPETENCIA = re.compile(r"^\d{1,2}$")

# Fila de Parametros → etiqueta normalizada de la columna A (D2).
ETIQUETAS = {
    1: "CODIGO MODULAR",
    2: "ANEXO",
    4: "ANO ACADEMICO",
    6: "PERIODO",
    7: "GRADO",
    8: "SECCION",
}
GRADOS = {"PRIMERO": 1, "SEGUNDO": 2, "TERCERO": 3, "CUARTO": 4, "QUINTO": 5, "SEXTO": 6}


class PlantillaNoReconocida(Exception):
    """El archivo no es la plantilla o no corresponde a la institución (D2, D9)."""

    def __init__(self, mensaje=NO_ES_LA_PLANTILLA):
        super().__init__(mensaje)


class ArchivoDemasiadoGrande(Exception):
    """Más de 3 MB: tiene su propio mensaje (spec «Otro tipo con nombre de Excel»)."""

    def __init__(self):
        super().__init__(DEMASIADO_GRANDE)


def clave(texto):
    """Forma de comparar nombres (D7): sin tildes, en mayúsculas, espacios colapsados y sin
    espacios junto a la coma."""
    sin_marcas = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)
    )
    colapsado = " ".join(sin_marcas.upper().split())
    return re.sub(r"\s*,\s*", ",", colapsado)


@dataclass(frozen=True)
class Parametros:
    codigo_modular: str
    anexo: int
    anio: int
    periodo: str
    grado: int
    codigo_seccion: str
    nombre_seccion: str


@dataclass
class HojaDeArea:
    """Una hoja de área: su código, la columna «NL» de cada número de competencia y las filas
    con nombre ``(fila, nombre)``. La conclusión va en la columna siguiente a la de «NL»."""

    nombre: str
    codigo: str
    competencias: dict[int, int] = field(default_factory=dict)
    filas: list[tuple[int, str]] = field(default_factory=list)


def _vacia(valor):
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _entero(valor):
    """2, 2.0 o «2» → 2; cualquier otra cosa no se reconoce."""
    if isinstance(valor, bool):
        raise PlantillaNoReconocida
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor.strip())
    raise PlantillaNoReconocida


def _texto(valor):
    if _vacia(valor):
        raise PlantillaNoReconocida
    return str(valor).strip()


def _etiqueta(valor):
    return clave(valor or "").rstrip(":").strip()


def _revisar_paquete(contenido):
    """D9: zip, lo descomprimido, la cantidad de partes y que no tenga macros."""
    if not contenido or not zipfile.is_zipfile(io.BytesIO(contenido)):
        raise PlantillaNoReconocida
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        partes = paquete.infolist()
        if len(partes) > LIMITE_PARTES:
            raise PlantillaNoReconocida
        if sum(parte.file_size for parte in partes) > LIMITE_DESCOMPRIMIDO:
            raise PlantillaNoReconocida
        if any(parte.filename.lower().endswith("vbaproject.bin") for parte in partes):
            raise PlantillaNoReconocida
        tipos = ElementTree.fromstring(paquete.read("[Content_Types].xml"))
    principales = [
        nodo.get("ContentType", "")
        for nodo in tipos.iter(f"{TIPOS_DE_CONTENIDO}Override")
        if nodo.get("ContentType", "").endswith(".main+xml")
    ]
    if principales != [XLSX_MAIN]:
        raise PlantillaNoReconocida


def _leer_parametros(ws):
    for fila, esperada in ETIQUETAS.items():
        if _etiqueta(ws.cell(fila, 1).value) != esperada:
            raise PlantillaNoReconocida
    codigo = ws["B1"].value
    if isinstance(codigo, (int, float)) and not isinstance(codigo, bool):
        codigo = f"{_entero(codigo):07d}"
    codigo_seccion = ws["B8"].value
    if isinstance(codigo_seccion, (int, float)) and not isinstance(codigo_seccion, bool):
        codigo_seccion = f"{_entero(codigo_seccion):02d}"
    grado = GRADOS.get(_etiqueta(ws["C7"].value))
    if grado is None:
        raise PlantillaNoReconocida
    return Parametros(
        codigo_modular="".join(_texto(codigo).split()),
        anexo=_entero(ws["B2"].value),
        anio=_entero(ws["B4"].value),
        periodo=_texto(ws["B6"].value).upper(),
        grado=grado,
        codigo_seccion=_texto(codigo_seccion),
        nombre_seccion=_texto(ws["C8"].value),
    )


def _leer_hoja(ws):
    coincidencia = HOJA_DE_AREA.match(ws.title)
    if coincidencia is None:
        raise PlantillaNoReconocida
    hoja = HojaDeArea(nombre=ws.title, codigo=coincidencia.group(1))
    columna_nombres = None
    for celda in ws[1]:
        valor = celda.value
        if _etiqueta(valor) == "NOMBRES":
            columna_nombres = celda.column
            continue
        if isinstance(valor, int) and not isinstance(valor, bool):
            valor = str(valor)
        if not (isinstance(valor, str) and NUMERO_COMPETENCIA.match(valor.strip())):
            continue
        numero = int(valor.strip())
        columna = celda.column
        if (
            numero < 1
            or numero in hoja.competencias
            or _etiqueta(ws.cell(2, columna).value) != "NL"
            or not _etiqueta(ws.cell(2, columna + 1).value).startswith("CONCLUSION")
        ):
            raise PlantillaNoReconocida
        hoja.competencias[numero] = columna
    if columna_nombres is None:
        raise PlantillaNoReconocida
    for fila in range(PRIMERA_FILA, PRIMERA_FILA + FILAS_MAXIMAS):
        nombre = ws.cell(fila, columna_nombres).value
        if _vacia(nombre):
            break
        hoja.filas.append((fila, " ".join(str(nombre).split())))
    return hoja


class Libro:
    """El libro abierto, con sus parámetros y sus hojas de área ya leídos."""

    def __init__(self, wb):
        self._wb = wb
        if "Parametros" not in wb.sheetnames:
            raise PlantillaNoReconocida
        if wb.chartsheets:
            raise PlantillaNoReconocida
        self.parametros = _leer_parametros(wb["Parametros"])
        self.hojas = [_leer_hoja(ws) for ws in wb.worksheets if ws.title not in HOJAS_FIJAS]

    def escribir(self, hoja, fila, columna, valor):
        """Escribe ``valor`` (``None`` la vacía) y dice si la celda tenía otro valor no vacío,
        también una fórmula (D8)."""
        celda = self._wb[hoja].cell(fila, columna)
        if isinstance(celda, MergedCell):  # Solo lectura en openpyxl: no es la plantilla.
            raise PlantillaNoReconocida
        anterior = celda.value
        celda.value = valor
        return not _vacia(anterior) and anterior != valor

    def guardar(self):
        salida = io.BytesIO()
        self._wb.save(salida)
        return salida.getvalue()


def abrir(contenido):
    """El ``Libro`` de ``contenido`` (bytes), o ``PlantillaNoReconocida`` sin el error original."""
    if len(contenido) > LIMITE_BYTES:
        raise ArchivoDemasiadoGrande
    try:
        _revisar_paquete(contenido)
        wb = load_workbook(io.BytesIO(contenido), data_only=False, keep_vba=False)
        return Libro(wb)
    except PlantillaNoReconocida:
        raise
    except Exception:  # noqa: BLE001 - cualquier fallo del zip o de openpyxl es «no es la plantilla» (D9)
        raise PlantillaNoReconocida from None
