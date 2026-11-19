"""Generador de plantillas ficticias «Periodo por Excel» del SIAGIE (US-024/025, design D12).

Arma con openpyxl un libro con la forma de la muestra: ``Generalidades``, ``Parametros`` oculta
(etiquetas en la columna A, valores en B y C) y una hoja por área con «ID», «Cód. Estudiante»,
«Nombres» y el número de cada competencia sobre dos columnas combinadas, «NL» y «Conclusión
descriptiva de la competencia» debajo, estudiantes desde la fila 3, validaciones y leyenda.
Código modular, nombres y textos son ficticios; ningún archivo binario entra al repo.
"""

import io
import zipfile

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Código modular ficticio de las pruebas (siete dígitos, como el del SIAGIE).
CODIGO_MODULAR = "0999991"

ETIQUETAS = {
    "codigo": "Código Modular:",
    "anexo": "Anexo:",
    "nivel": "Nivel:",
    "anio": "Año Académico :",
    "diseno": "Diseño Curricular :",
    "periodo": "Periodo :",
    "grado": "Grado :",
    "seccion": "Sección :",
}

# Matemática (cuatro competencias) y Comunicación (tres), como en la muestra.
HOJAS = {"063-MATE": 4, "0005-COMU": 3}

NOMBRES = ["PAREDES SOTO, NOA", "VILCA RAMOS, ELIO"]

CONCLUSION_HOJA = "Conclusión descriptiva de la competencia"
FILAS_MINIMAS = 13
XLSX_MAIN = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
XLSM_MAIN = "application/vnd.ms-excel.sheet.macroEnabled.main+xml"


def _numeros(valor):
    """``4`` → «01»…«04»; una lista se usa tal cual (para el orden o números raros)."""
    if isinstance(valor, int):
        return [f"{n:02d}" for n in range(1, valor + 1)]
    return list(valor)


def _parametros(ws, campos, etiquetas):
    filas = [
        ("codigo", campos["codigo_modular"], 30954),
        ("anexo", campos["anexo"], None),
        ("nivel", "B0", "Primaria"),
        ("anio", campos["anio"], None),
        ("diseno", "20", "CURRÍCULO NACIONAL 2017"),
        ("periodo", campos["periodo"], campos["texto_periodo"]),
        ("grado", "05", campos["grado"]),
        ("seccion", campos["codigo_seccion"], campos["nombre_seccion"]),
    ]
    for numero, (clave, valor_b, valor_c) in enumerate(filas, start=1):
        ws.cell(numero, 1, etiquetas[clave])
        ws.cell(numero, 2, valor_b)
        if valor_c is not None:
            ws.cell(numero, 3, valor_c)
    ws.sheet_state = "hidden"


def _hoja_de_area(ws, numeros, nombres):
    for columna, texto in enumerate(["ID", "Cód. Estudiante", "Nombres"], start=1):
        ws.cell(1, columna, texto)
        ws.merge_cells(start_row=1, start_column=columna, end_row=2, end_column=columna)
    ultima = 2 + max(len(nombres), FILAS_MINIMAS)
    niveles = DataValidation(type="list", formula1='"A,AD,B,C"', allow_blank=True)
    conclusiones = DataValidation(type="textLength", operator="between", formula1="10")
    conclusiones.formula2 = "500"
    for indice, numero in enumerate(numeros):
        columna = 4 + 2 * indice
        ws.cell(1, columna, numero)
        ws.merge_cells(start_row=1, start_column=columna, end_row=1, end_column=columna + 1)
        ws.cell(2, columna, "NL")
        ws.cell(2, columna + 1, CONCLUSION_HOJA)
        letra, siguiente = get_column_letter(columna), get_column_letter(columna + 1)
        niveles.add(f"{letra}3:{letra}{ultima}")
        conclusiones.add(f"{siguiente}3:{siguiente}{ultima}")
    ws.add_data_validation(niveles)
    ws.add_data_validation(conclusiones)
    for fila, nombre in enumerate(nombres, start=3):
        ws.cell(fila, 1, f"ID-{fila:03d}")
        ws.cell(fila, 2, f"COD-{fila:03d}")
        ws.cell(fila, 3, nombre)
    leyenda = ultima + 3
    ws.cell(leyenda, 2, "LEYENDA")
    ws.cell(leyenda + 1, 2, "NL = Nivel de logro alcanzado")
    ws.merge_cells(start_row=leyenda + 1, start_column=2, end_row=leyenda + 1, end_column=3)


def generar(
    *,
    codigo_modular=CODIGO_MODULAR,
    anexo=0,
    anio=2027,
    periodo="B3",
    texto_periodo="TERCER BIMESTRE",
    grado="SEGUNDO",
    codigo_seccion="01",
    nombre_seccion="TRIUNFADORES",
    hojas=None,
    nombres=None,
    celdas=None,
    etiquetas=None,
    sin_parametros=False,
    nl_debajo=True,
):
    """Los bytes de una plantilla ficticia.

    ``hojas``: nombre de hoja → cantidad de competencias o lista de números. ``nombres``: los
    de la columna «Nombres», desde la fila 3, en todas las hojas. ``celdas``: «hoja!B3» → valor
    que ya trae la plantilla. ``etiquetas``: reemplaza las de la columna A de Parametros.
    ``nl_debajo=False`` quita el «NL» de la primera competencia de cada hoja.
    """
    hojas = HOJAS if hojas is None else hojas
    nombres = NOMBRES if nombres is None else nombres
    wb = Workbook()
    generalidades = wb.active
    generalidades.title = "Generalidades"
    generalidades["B2"] = "DATOS GENERALES :"
    generalidades.merge_cells("B4:J4")
    if not sin_parametros:
        _parametros(
            wb.create_sheet("Parametros"),
            {
                "codigo_modular": codigo_modular,
                "anexo": anexo,
                "anio": anio,
                "periodo": periodo,
                "texto_periodo": texto_periodo,
                "grado": grado,
                "codigo_seccion": codigo_seccion,
                "nombre_seccion": nombre_seccion,
            },
            {**ETIQUETAS, **(etiquetas or {})},
        )
    for nombre_hoja, competencias in hojas.items():
        ws = wb.create_sheet(nombre_hoja)
        _hoja_de_area(ws, _numeros(competencias), nombres)
        if not nl_debajo:
            ws.cell(2, 4).value = None
    for referencia, valor in (celdas or {}).items():
        nombre_hoja, coordenada = referencia.split("!")
        wb[nombre_hoja][coordenada] = valor
    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


def rehacer_zip(contenido, cambiar=None, agregar=None):
    """Otro zip con las partes de ``contenido``: ``cambiar`` (parte → función sobre sus bytes)
    y ``agregar`` (parte → bytes). Para las pruebas de archivos hostiles."""
    salida = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(contenido)) as origen,
        zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as destino,
    ):
        for parte in origen.infolist():
            datos = origen.read(parte.filename)
            if cambiar and parte.filename in cambiar:
                datos = cambiar[parte.filename](datos)
            destino.writestr(parte.filename, datos)
        for nombre, datos in (agregar or {}).items():
            destino.writestr(nombre, datos)
    return salida.getvalue()


def con_macros(contenido):
    """La plantilla convertida en libro con macros (.xlsm con nombre de .xlsx)."""
    return rehacer_zip(
        contenido,
        cambiar={
            "[Content_Types].xml": lambda datos: datos.replace(
                XLSX_MAIN.encode(), XLSM_MAIN.encode()
            )
        },
        agregar={"xl/vbaProject.bin": b"\x00" * 64},
    )
