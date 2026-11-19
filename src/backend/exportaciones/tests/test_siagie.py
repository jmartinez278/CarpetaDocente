"""Lectura y escritura del libro del SIAGIE, sin base de datos (US-024/025, design D2, D7 a D9).

Las plantillas son ficticias y se generan en cada prueba (D12).
"""

import io

import openpyxl
import pytest
from openpyxl import load_workbook

from exportaciones import siagie
from exportaciones.tests.plantilla import CODIGO_MODULAR, con_macros, generar, rehacer_zip

# --- Parametros (D2) ---


def test_lee_los_parametros_de_la_plantilla():
    libro = siagie.abrir(generar())

    assert libro.parametros == siagie.Parametros(
        codigo_modular=CODIGO_MODULAR,
        anexo=0,
        anio=2027,
        periodo="B3",
        grado=2,
        codigo_seccion="01",
        nombre_seccion="TRIUNFADORES",
    )


def test_el_codigo_modular_como_numero_se_completa_a_siete_digitos():
    libro = siagie.abrir(generar(codigo_modular=999991, anexo=2.0, anio=2027.0))

    assert libro.parametros.codigo_modular == CODIGO_MODULAR
    assert libro.parametros.anexo == 2
    assert libro.parametros.anio == 2027


def test_el_codigo_modular_con_espacios_se_limpia():
    libro = siagie.abrir(generar(codigo_modular=f" {CODIGO_MODULAR} "))

    assert libro.parametros.codigo_modular == CODIGO_MODULAR


@pytest.mark.parametrize(
    ("texto", "numero"),
    [("PRIMERO", 1), ("SEGUNDO", 2), ("TERCERO", 3), ("CUARTO", 4), ("QUINTO", 5), ("SEXTO", 6)],
)
def test_el_grado_en_texto_es_un_numero(texto, numero):
    assert siagie.abrir(generar(grado=texto)).parametros.grado == numero


def test_las_etiquetas_se_comparan_sin_tildes_mayusculas_ni_dos_puntos():
    libro = siagie.abrir(generar(etiquetas={"codigo": "codigo modular", "seccion": "SECCION:"}))

    assert libro.parametros.nombre_seccion == "TRIUNFADORES"


# --- Rechazos (D2, D9) ---


def _no_se_reconoce(contenido):
    with pytest.raises(siagie.PlantillaNoReconocida) as error:
        siagie.abrir(contenido)
    assert str(error.value) == siagie.NO_ES_LA_PLANTILLA
    return error.value


@pytest.mark.parametrize("clave", ["codigo", "anexo", "anio", "periodo", "grado", "seccion"])
def test_una_etiqueta_cambiada_no_se_reconoce(clave):
    _no_se_reconoce(generar(etiquetas={clave: "Otra cosa:"}))


def test_sin_la_hoja_parametros_no_se_reconoce():
    _no_se_reconoce(generar(sin_parametros=True))


@pytest.mark.parametrize("campo", ["anexo", "anio"])
def test_un_numero_que_no_es_numero_no_se_reconoce(campo):
    _no_se_reconoce(generar(**{campo: "dos"}))


def test_un_grado_que_no_es_de_primaria_no_se_reconoce():
    _no_se_reconoce(generar(grado="SETIMO"))


def test_una_hoja_con_nombre_sin_codigo_no_se_reconoce():
    _no_se_reconoce(generar(hojas={"063-MATE": 4, "Notas": 2}))


def test_un_numero_de_competencia_sin_nl_debajo_no_se_reconoce():
    _no_se_reconoce(generar(nl_debajo=False))


def test_una_hoja_sin_la_columna_nombres_no_se_reconoce():
    contenido = generar()
    wb = load_workbook(io.BytesIO(contenido))
    wb["063-MATE"].unmerge_cells("C1:C2")
    wb["063-MATE"]["C1"] = "Alumno"
    salida = io.BytesIO()
    wb.save(salida)

    _no_se_reconoce(salida.getvalue())


def test_un_numero_repetido_en_la_hoja_no_se_reconoce():
    _no_se_reconoce(generar(hojas={"063-MATE": ["01", "01"]}))


def test_un_pdf_renombrado_no_se_reconoce():
    _no_se_reconoce(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF")


def test_un_archivo_vacio_no_se_reconoce():
    _no_se_reconoce(b"")


def test_un_zip_que_no_es_un_libro_no_se_reconoce():
    _no_se_reconoce(rehacer_zip(generar(), cambiar={"xl/workbook.xml": lambda _: b"<roto"}))


def test_un_zip_que_se_infla_por_encima_del_limite_no_se_reconoce():
    relleno = b"\0" * (siagie.LIMITE_DESCOMPRIMIDO + 1)
    contenido = rehacer_zip(generar(), agregar={"xl/media/relleno.bin": relleno})

    assert len(contenido) < siagie.LIMITE_BYTES
    _no_se_reconoce(contenido)


def test_un_zip_con_mas_de_300_partes_no_se_reconoce():
    partes = {f"xl/media/p{n}.txt": b"x" for n in range(siagie.LIMITE_PARTES)}

    _no_se_reconoce(rehacer_zip(generar(), agregar=partes))


def test_un_libro_con_macros_no_se_reconoce():
    _no_se_reconoce(con_macros(generar()))


def test_mas_de_4_mb_tiene_su_propio_mensaje():
    with pytest.raises(siagie.ArchivoDemasiadoGrande) as error:
        siagie.abrir(b"x" * (siagie.LIMITE_BYTES + 1))

    assert str(error.value) == "El archivo supera los 4 MB. Elige uno más pequeño."


def test_el_mensaje_del_rechazo_no_lleva_el_error_de_openpyxl():
    error = _no_se_reconoce(rehacer_zip(generar(), cambiar={"xl/workbook.xml": lambda _: b"<x"}))

    assert error.__cause__ is None
    assert error.__suppress_context__


def test_openpyxl_usa_defusedxml():
    """La documentación de openpyxl lo pide contra *billion laughs* (D9)."""
    assert openpyxl.DEFUSEDXML


# --- Hojas de área y filas (D2, D7) ---


def test_cada_hoja_de_area_trae_su_codigo_y_sus_competencias_por_columna():
    libro = siagie.abrir(generar(hojas={"063-MATE": ["02", "01", "03"], "0005-COMU": 1}))

    mate, comu = libro.hojas
    assert (mate.nombre, mate.codigo) == ("063-MATE", "063")
    assert mate.competencias == {2: 4, 1: 6, 3: 8}
    assert (comu.codigo, comu.competencias) == ("0005", {1: 4})


def test_las_filas_van_hasta_la_primera_sin_nombre():
    nombres = ["PAREDES SOTO, NOA", "  VILCA RAMOS, ELIO ", "", "QUISPE, ANA"]

    (hoja,) = siagie.abrir(generar(hojas={"063-MATE": 1}, nombres=nombres)).hojas

    assert hoja.filas == [(3, "PAREDES SOTO, NOA"), (4, "VILCA RAMOS, ELIO")]


def test_lee_hasta_60_filas():
    nombres = [f"APELLIDO{n:02d}, NOMBRE" for n in range(65)]

    (hoja,) = siagie.abrir(generar(hojas={"063-MATE": 1}, nombres=nombres)).hojas

    assert len(hoja.filas) == siagie.FILAS_MAXIMAS == 60


def test_un_libro_sin_hojas_de_area_se_abre_sin_hojas():
    assert siagie.abrir(generar(hojas={})).hojas == []


# --- Clave de nombre (D7) ---


@pytest.mark.parametrize(
    ("texto", "clave"),
    [
        ("Pérez  Quispe , María", "PEREZ QUISPE,MARIA"),
        ("PEREZ QUISPE, MARIA", "PEREZ QUISPE,MARIA"),
        ("  peña ñahui ,  josé  ", "PENA NAHUI,JOSE"),
        ("TRIUNFADORES", "TRIUNFADORES"),
    ],
)
def test_la_clave_quita_tildes_mayusculas_y_espacios(texto, clave):
    assert siagie.clave(texto) == clave


# --- Escritura e ida y vuelta (D8) ---


def test_escribir_dice_si_la_celda_tenia_otro_valor():
    libro = siagie.abrir(
        generar(
            celdas={
                "063-MATE!D3": "A",
                "063-MATE!F3": "B",
                "063-MATE!H3": "='0005-COMU'!D3",
                "063-MATE!E3": "Texto anterior de prueba.",
            }
        )
    )

    assert libro.escribir("063-MATE", 3, 4, "B") is True
    assert libro.escribir("063-MATE", 3, 6, "B") is False
    assert libro.escribir("063-MATE", 3, 8, "A") is True
    assert libro.escribir("063-MATE", 3, 5, None) is True
    assert libro.escribir("063-MATE", 3, 10, "AD") is False
    assert libro.escribir("063-MATE", 3, 11, None) is False


def test_ida_y_vuelta_conserva_la_hoja_oculta_las_validaciones_y_lo_no_tocado():
    contenido = generar(celdas={"063-MATE!F4": "C", "0005-COMU!D3": "AD"})
    antes = load_workbook(io.BytesIO(contenido))

    libro = siagie.abrir(contenido)
    libro.escribir("063-MATE", 3, 4, "B")
    libro.escribir("063-MATE", 3, 5, "Conclusión ficticia para la prueba.")
    despues = load_workbook(io.BytesIO(libro.guardar()))

    assert despues.sheetnames == antes.sheetnames
    assert despues["Parametros"].sheet_state == "hidden"
    assert despues["063-MATE"]["D3"].value == "B"
    assert despues["063-MATE"]["E3"].value == "Conclusión ficticia para la prueba."
    for hoja in antes.worksheets:
        otra = despues[hoja.title]
        validaciones = [
            (v.type, v.formula1, v.formula2, str(v.sqref))
            for v in hoja.data_validations.dataValidation
        ]
        assert validaciones == [
            (v.type, v.formula1, v.formula2, str(v.sqref))
            for v in otra.data_validations.dataValidation
        ]
        assert set(map(str, hoja.merged_cells.ranges)) == set(map(str, otra.merged_cells.ranges))
        for fila in hoja.iter_rows():
            for celda in fila:
                if (hoja.title, celda.coordinate) not in {("063-MATE", "D3"), ("063-MATE", "E3")}:
                    assert otra[celda.coordinate].value == celda.value
