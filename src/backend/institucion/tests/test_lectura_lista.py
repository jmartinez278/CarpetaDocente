"""Pruebas de la lectura del texto pegado (spec estudiantes-seccion; design de US-006, D3).

Función pura: no usa la base de datos.
"""

import pytest

from institucion.servicios import leer_lista_pegada


def motivos(texto):
    """Pares (líneas, motivo) de los errores de formato del texto."""
    _, errores = leer_lista_pegada(texto)
    return [(error.lineas, error.motivo) for error in errores]


# --- Filas válidas y líneas en blanco ---


def test_una_linea_valida_da_su_fila_normalizada():
    filas, errores = leer_lista_pegada("quispe  mamani, ana lucía")

    assert filas == [(1, "QUISPE MAMANI", "ANA LUCÍA")]
    assert errores == []


def test_las_lineas_en_blanco_se_ignoran_pero_cuentan_en_la_numeracion():
    texto = "\n\nAGUILAR, LUCIANA\n\nRAMOS, VALENTIN\n\n"

    filas, errores = leer_lista_pegada(texto)

    assert [fila[0] for fila in filas] == [3, 5]
    assert errores == []


@pytest.mark.parametrize("blanco", ["   ", "\t", " \t \t", " "])
def test_la_linea_de_solo_espacios_o_tabulaciones_es_blanca(blanco):
    texto = f"AGUILAR, LUCIANA\n{blanco}\nRAMOS, VALENTIN"

    filas, errores = leer_lista_pegada(texto)

    assert [fila[0] for fila in filas] == [1, 3]
    assert errores == []


def test_texto_vacio_no_da_filas_ni_errores():
    assert leer_lista_pegada("") == ([], [])
    assert leer_lista_pegada(" \n\t\n ") == ([], [])


# --- Motivos de formato, uno por línea ---


@pytest.mark.parametrize(
    "linea",
    [
        "ALVARADO ROJAS\tMARÍA FERNANDA\t2.º A",
        "ALVARADO ROJAS,\tMARÍA FERNANDA\t2.º A",
        "ALVARADO ROJAS\tMARÍA",
        "\tALVARADO ROJAS, MARÍA",
    ],
)
def test_linea_con_tabulacion_pide_pegar_solo_la_columna(linea):
    assert motivos(f"AGUILAR, LUCIANA\nRAMOS, VALENTIN\n{linea}") == [
        ((3,), "pega solo la columna de apellidos y nombres")
    ]


def test_linea_sin_coma():
    assert motivos("CONDORI MAMANI DANIELA") == [((1,), "falta la coma entre apellidos y nombres")]


def test_linea_con_mas_de_una_coma():
    assert motivos("CONDORI, MAMANI, DANIELA") == [((1,), "tiene más de una coma")]


def test_apellidos_vacios():
    assert motivos(", DANIELA") == [((1,), "faltan los apellidos")]
    assert motivos("   , DANIELA") == [((1,), "faltan los apellidos")]


def test_nombres_vacios():
    assert motivos("CONDORI MAMANI,") == [((1,), "faltan los nombres")]
    assert motivos("CONDORI MAMANI,   ") == [((1,), "faltan los nombres")]


def test_coma_sola_tiene_un_solo_motivo():
    assert motivos(",") == [((1,), "faltan los apellidos")]


def test_la_linea_con_error_no_da_fila():
    filas, errores = leer_lista_pegada("AGUILAR, LUCIANA\nCONDORI MAMANI DANIELA")

    assert filas == [(1, "AGUILAR", "LUCIANA")]
    assert len(errores) == 1


def test_cada_error_lleva_su_ayuda_y_su_titulo():
    _, errores = leer_lista_pegada("AGUILAR, LUCIANA\nCONDORI MAMANI DANIELA")

    error = errores[0]
    assert error.titulo == "Línea 2: falta la coma entre apellidos y nombres"
    assert error.ayuda == "Separa los apellidos de los nombres con una coma."


def test_los_errores_van_en_orden_de_linea():
    assert [e[0] for e in motivos("A B\nC, D\nE F\nG, H, I")] == [(1,), (3,), (4,)]


# --- Finales de línea y numeración ---


@pytest.mark.parametrize("final", ["\r\n", "\r", "\n"])
def test_los_finales_de_linea_no_desfasan_la_numeracion(final):
    texto = final.join(["AGUILAR, LUCIANA", "", "CONDORI MAMANI DANIELA"])

    assert motivos(texto) == [((3,), "falta la coma entre apellidos y nombres")]


def test_u2028_dentro_de_una_linea_no_la_parte():
    texto = "AGUILAR, LUCIANA\nCONDORI MAMANI DANIELA\nRAMOS VALENTIN"

    assert motivos(texto) == [
        ((2,), "falta la coma entre apellidos y nombres"),
        ((3,), "falta la coma entre apellidos y nombres"),
    ]


# --- Máximo de 60 líneas ---


def test_61_lineas_con_texto_da_solo_el_error_de_60():
    texto = "\n".join(f"APELLIDO{i}, NOMBRE{i}" for i in range(61)) + "\nsin coma"

    filas, errores = leer_lista_pegada(texto)

    assert filas == []
    assert len(errores) == 1
    assert errores[0].titulo == "La lista tiene 62 líneas; el máximo es 60"
    assert errores[0].ayuda == "Pega solo los estudiantes de tu sección."


def test_las_lineas_en_blanco_no_cuentan_para_el_maximo():
    texto = "\n\n".join(f"APELLIDO{i}, NOMBRE{i}" for i in range(60))

    filas, errores = leer_lista_pegada(texto)

    assert len(filas) == 60
    assert errores == []
