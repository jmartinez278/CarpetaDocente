"""Cruzar estudiantes, llenar, contar y registrar (US-024/025, design D7, D8, D11).

Specs «Estudiantes de la plantilla», «Llenado de la plantilla», «Sin notas en el periodo»,
«Resumen del llenado», «El archivo no se guarda» y, en registro-actividad, «Plantilla del SIAGIE
completada». Todos los nombres son ficticios.
"""

import io

import pytest
from django.apps import apps
from django.core.files.storage import Storage
from django.db import models
from openpyxl import load_workbook

from actividad.models import Operacion, RegistroActividad
from exportaciones import servicios
from exportaciones.models import EquivalenciaSeccion
from exportaciones.tests.plantilla import generar
from institucion.models import Estudiante, Seccion
from notas.tests.conftest import (
    COMUNICACION,
    CONCLUSION,
    EDUCACION_FISICA,
    MATEMATICA,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)

pytestmark = pytest.mark.django_db

MARIA = "PÉREZ QUISPE, MARÍA"
LUIS = "ROJAS LIMA, LUIS"
EVA = "SOTO VERA, EVA"
AJENA = "DE LA LOMA DE PAPEL, AMARANTA LUZ"
OTRA_CONCLUSION = "Explica con apoyo sus estrategias de conteo."


@pytest.fixture
def b3(bimestres):
    return bimestres[2]


@pytest.fixture
def alumnos(seccion_tutora, ie_siagie):
    """María y Luis activos y Eva trasladada, en 2.º A con su tutora."""
    maria, luis = crear_estudiantes(seccion_tutora, MARIA, LUIS)
    (eva,) = crear_estudiantes(seccion_tutora, EVA, estado=Estudiante.Estado.TRASLADADO)
    return maria, luis, eva


@pytest.fixture
def notas_b3(seccion_tutora, alumnos, b3):
    """Matemática y Comunicación marcadas en B3. María: B en C1 y AD en C2; Luis: A en C3;
    Eva (trasladada): C en C1 con otra conclusión."""
    maria, luis, eva = alumnos
    marcar(seccion_tutora, b3, ids_de(MATEMATICA, COMUNICACION))
    poner_nota(maria, competencia(MATEMATICA, 1), b3, "B")
    poner_nota(maria, competencia(MATEMATICA, 2), b3, "AD")
    poner_nota(luis, competencia(MATEMATICA, 3), b3, "A")
    poner_nota(eva, competencia(MATEMATICA, 1), b3, "C", OTRA_CONCLUSION)
    return b3


def completar(usuario, seccion_id=None, **campos):
    campos.setdefault("nombre_seccion", "A")
    campos.setdefault("nombres", ["PEREZ QUISPE, MARIA", "ROJAS LIMA, LUIS"])
    campos.setdefault("hojas", {"063-MATE": 4})
    return servicios.completar_plantilla(usuario, generar(**campos), seccion_id)


def hoja(resumen, nombre="063-MATE"):
    return load_workbook(io.BytesIO(resumen.contenido))[nombre]


# --- Llenado de la plantilla (D8) ---


def test_camino_ideal(direccion, seccion_tutora, notas_b3):
    resumen = completar(direccion)

    mate = hoja(resumen)
    assert [mate[c].value for c in ("D3", "E3", "F3", "G3", "H3", "J3")] == [
        "B",
        CONCLUSION,
        "AD",
        None,
        None,
        None,
    ]
    assert (mate["H4"].value, mate["I4"].value) == ("A", None)
    assert resumen.seccion == seccion_tutora
    assert resumen.periodo == notas_b3
    assert (resumen.encontrados, resumen.no_encontrados, resumen.reemplazadas) == (2, [], 0)


def test_la_columna_sale_del_numero_y_no_de_la_posicion(direccion, notas_b3):
    mate = hoja(completar(direccion, hojas={"063-MATE": ["03", "01"]}))

    assert (mate["D4"].value, mate["F3"].value, mate["G3"].value) == ("A", "B", CONCLUSION)
    assert mate["D3"].value is None


def test_celda_con_otro_valor_o_formula_se_reemplaza_y_cuenta(direccion, notas_b3):
    resumen = completar(
        direccion,
        celdas={"063-MATE!D3": "A", "063-MATE!F3": "='0005-COMU'!D3", "063-MATE!H4": "A"},
    )

    mate = hoja(resumen)
    assert (mate["D3"].value, mate["F3"].value, mate["H4"].value) == ("B", "AD", "A")
    assert resumen.reemplazadas == 2


def test_ad_o_a_vacian_la_conclusion_que_traia_la_celda(direccion, notas_b3):
    resumen = completar(direccion, celdas={"063-MATE!G3": "Texto previo de la prueba."})

    assert hoja(resumen)["G3"].value is None
    assert resumen.reemplazadas == 1


def test_una_nota_que_no_tiene_no_toca_la_celda(direccion, notas_b3):
    resumen = completar(direccion, celdas={"063-MATE!J3": "A", "063-MATE!K3": "Otra de prueba."})

    mate = hoja(resumen)
    assert (mate["J3"].value, mate["K3"].value) == ("A", "Otra de prueba.")
    assert resumen.reemplazadas == 0


def test_no_escribe_pendiente_en_las_celdas_sin_nota(direccion, notas_b3):
    libro = load_workbook(io.BytesIO(completar(direccion, hojas={"063-MATE": 4}).contenido))

    valores = {celda.value for ws in libro.worksheets for fila in ws.iter_rows() for celda in fila}
    assert not any("Pendiente" in str(valor) for valor in valores)


def test_varias_hojas_y_el_resto_del_libro_queda_igual(direccion, notas_b3):
    resumen = completar(direccion, hojas={"063-MATE": 4, "0005-COMU": 3, "031-EFIS": 3})

    libro = load_workbook(io.BytesIO(resumen.contenido))
    assert libro.sheetnames == ["Generalidades", "Parametros", "063-MATE", "0005-COMU", "031-EFIS"]
    assert libro["Parametros"].sheet_state == "hidden"
    assert libro["063-MATE"]["D3"].value == "B"
    assert libro["0005-COMU"]["D3"].value is None


# --- Estudiantes de la plantilla (D7) ---


def test_estudiante_que_no_esta_en_la_seccion_va_una_vez_a_no_encontrados(direccion, notas_b3):
    resumen = completar(
        direccion,
        nombres=["PEREZ QUISPE, MARIA", AJENA, "ROJAS LIMA, LUIS"],
        hojas={"063-MATE": 4, "0005-COMU": 3},
        celdas={"063-MATE!D4": "C"},
    )

    assert resumen.no_encontrados == [AJENA]
    assert resumen.encontrados == 2
    assert hoja(resumen)["D4"].value == "C"
    assert hoja(resumen)["H5"].value == "A"


def test_sin_parecidos(direccion, seccion_tutora, ie_siagie, b3):
    (elena,) = crear_estudiantes(seccion_tutora, "PÉREZ QUISPE, MARÍA ELENA")
    poner_nota(elena, competencia(MATEMATICA, 1), b3, "A")

    resumen = completar(direccion, nombres=["PEREZ QUISPE, MARIA"])

    assert resumen.no_encontrados == ["PEREZ QUISPE, MARIA"]
    assert resumen.encontrados == 0
    assert hoja(resumen)["D3"].value is None


def test_un_homonimo_normalizado_no_se_toca(direccion, seccion_tutora, ie_siagie, b3):
    con_tilde, sin_tilde = crear_estudiantes(seccion_tutora, "PÉREZ, ANA", "PEREZ, ANA")
    poner_nota(con_tilde, competencia(MATEMATICA, 1), b3, "A")

    resumen = completar(direccion, nombres=["PEREZ, ANA"])

    assert resumen.no_encontrados == ["PEREZ, ANA"]
    assert hoja(resumen)["D3"].value is None


def test_un_trasladado_con_notas_se_completa(direccion, notas_b3):
    resumen = completar(direccion, nombres=["SOTO VERA, EVA"])

    assert (hoja(resumen)["D3"].value, hoja(resumen)["E3"].value) == ("C", OTRA_CONCLUSION)
    assert resumen.encontrados == 1


def test_un_nombre_sin_coma_se_compara_con_apellidos_y_nombres(direccion, notas_b3):
    resumen = completar(direccion, nombres=["Rojas  Lima Luis"])

    assert hoja(resumen)["H3"].value == "A"


def test_los_encontrados_son_estudiantes_distintos_en_todas_las_hojas(direccion, notas_b3):
    resumen = completar(
        direccion,
        nombres=["PEREZ QUISPE, MARIA", "ROJAS LIMA, LUIS", "SOTO VERA, EVA"],
        hojas={"063-MATE": 4, "0005-COMU": 3},
    )

    assert resumen.encontrados == 3


# --- Sin notas en el periodo ---


def test_periodo_sin_notas_no_devuelve_archivo_ni_deja_entrada(direccion, notas_b3):
    with pytest.raises(servicios.SinNotasEnElPeriodo) as error:
        completar(direccion, periodo="B4")

    assert str(error.value) == "No hay notas para completar en este periodo"
    assert not RegistroActividad.objects.filter(
        operacion=Operacion.PLANTILLA_SIAGIE_COMPLETADA
    ).exists()


def test_equivalencia_de_un_periodo_sin_notas_no_se_guarda(direccion, notas_b3, anio_abierto):
    b = Seccion.objects.create(anio_escolar=anio_abierto, grado=2, nombre="B")

    with pytest.raises(servicios.SinNotasEnElPeriodo):
        completar(direccion, b.pk, nombre_seccion="TRIUNFADORES")

    assert not EquivalenciaSeccion.objects.exists()
    assert not RegistroActividad.objects.exists()


# --- Faltantes y resumen ---


def test_faltantes_con_la_regla_de_la_hoja_de_notas(direccion, notas_b3, seccion_tutora, b3):
    """Activos (María y Luis) por competencias marcadas, menos sus notas: Matemática 4 × 2 − 3
    y Comunicación 3 × 2. Eva (trasladada) no suma."""
    assert completar(direccion).faltantes == 5 + 6


def test_un_area_a_cargo_del_docente_de_curso_no_suma(
    direccion, notas_b3, seccion_tutora, b3, areas_a_cargo
):
    marcar(seccion_tutora, b3, ids_de(EDUCACION_FISICA))

    assert completar(direccion).faltantes == 11


def test_sin_docente_de_aula_no_hay_faltantes(direccion, notas_b3, seccion_tutora):
    Seccion.objects.filter(pk=seccion_tutora.pk).update(docente=None)

    assert completar(direccion).faltantes == 0


def test_con_observaciones(direccion, notas_b3):
    resumen = completar(direccion, nombres=["PEREZ QUISPE, MARIA", AJENA])

    assert resumen.observaciones
    assert resumen.titulo == "Plantilla completada con observaciones"


def test_solo_faltantes_tambien_son_observaciones(direccion, notas_b3):
    resumen = completar(direccion)

    assert (resumen.no_encontrados, resumen.faltantes > 0) == ([], True)
    assert resumen.titulo == "Plantilla completada con observaciones"


def test_sin_observaciones_los_cuatro_conteos_en_cero(direccion, seccion_tutora, alumnos, b3):
    maria, luis, _ = alumnos
    c1 = competencia(MATEMATICA, 1)
    marcar(seccion_tutora, b3, {c1.pk})
    poner_nota(maria, c1, b3, "A")
    poner_nota(luis, c1, b3, "AD")

    resumen = completar(direccion, celdas={"063-MATE!D3": "A"})

    assert (resumen.no_encontrados, resumen.faltantes, resumen.reemplazadas) == ([], 0, 0)
    assert not resumen.observaciones
    assert resumen.titulo == "Plantilla completada"


def test_el_resumen_lleva_la_seccion_del_siagie_como_viene(
    direccion, notas_b3, secciones_de_segundo
):
    resumen = completar(direccion, secciones_de_segundo[0].pk, nombre_seccion="Triunfadores")

    assert (resumen.grado_siagie, resumen.nombre_siagie) == (2, "Triunfadores")
    assert resumen.anio == 2027


# --- Registro (D11) ---


def test_plantilla_completada_deja_su_entrada_sin_nombres(direccion, seccion_tutora, notas_b3):
    completar(
        direccion,
        nombres=["PEREZ QUISPE, MARIA", AJENA, "ROJAS LIMA, LUIS"],
        celdas={"063-MATE!D3": "A"},
    )

    entrada = RegistroActividad.objects.get(operacion=Operacion.PLANTILLA_SIAGIE_COMPLETADA)
    assert (entrada.usuario, entrada.entidad, entrada.entidad_id) == (
        direccion,
        "seccion",
        str(seccion_tutora.pk),
    )
    assert entrada.detalle == {
        "periodo": 3,
        "anio": 2027,
        "encontrados": 2,
        "no_encontrados": 1,
        "faltantes": 11,
        "reemplazadas": 1,
        "equivalencia": False,
    }


def test_con_equivalencia_nueva_el_detalle_lo_dice_sin_el_nombre_del_siagie(
    direccion, notas_b3, secciones_de_segundo
):
    a = secciones_de_segundo[0]

    resumen = completar(direccion, a.pk, nombre_seccion="TRIUNFADORES")

    entrada = RegistroActividad.objects.get(operacion=Operacion.PLANTILLA_SIAGIE_COMPLETADA)
    assert entrada.detalle["equivalencia"] is True
    assert "TRIUNFADORES" not in str(entrada.detalle)
    assert EquivalenciaSeccion.objects.get().seccion == a
    assert resumen.equivalencia_id == EquivalenciaSeccion.objects.get().pk


def test_una_completada_que_no_cabe_en_la_respuesta_no_guarda_nada(
    direccion, notas_b3, secciones_de_segundo, monkeypatch
):
    """En base64 debe caber en los 4,5 MB de una respuesta de Vercel; si no, nada queda guardado:
    ni la equivalencia nueva ni la entrada (hallazgo de Codex de la parte D)."""
    pesada = b"0" * (servicios.siagie.LIMITE_BYTES + 1)
    monkeypatch.setattr(servicios.siagie.Libro, "guardar", lambda libro: pesada)

    with pytest.raises(servicios.CompletadaDemasiadoGrande) as error:
        completar(direccion, secciones_de_segundo[0].pk, nombre_seccion="TRIUNFADORES")

    assert str(error.value) == (
        "La plantilla completada supera los 3 MB y no se puede descargar. "
        "No se guardó ningún cambio."
    )
    assert not EquivalenciaSeccion.objects.exists()
    assert not RegistroActividad.objects.exists()


def test_una_completada_justo_en_el_limite_se_entrega(direccion, notas_b3, monkeypatch):
    justa = b"0" * servicios.siagie.LIMITE_BYTES
    monkeypatch.setattr(servicios.siagie.Libro, "guardar", lambda libro: justa)

    assert completar(direccion).contenido == justa


def test_un_archivo_rechazado_no_deja_entrada(direccion, notas_b3):
    with pytest.raises(servicios.PlantillaNoReconocida):
        completar(direccion, codigo_modular="0999992")

    assert not RegistroActividad.objects.exists()


def test_una_eleccion_pendiente_no_deja_entrada(direccion, notas_b3, secciones_de_segundo):
    with pytest.raises(servicios.EligeSeccion):
        completar(direccion, nombre_seccion="TRIUNFADORES")

    assert not RegistroActividad.objects.exists()
    assert not EquivalenciaSeccion.objects.exists()


# --- El archivo no se guarda (Ley 29733) ---


def test_ni_el_archivo_ni_los_nombres_de_la_plantilla_quedan_guardados(
    direccion, notas_b3, monkeypatch
):
    guardados = []
    original = Storage.save
    monkeypatch.setattr(
        Storage, "save", lambda self, *a, **k: guardados.append(a) or original(self, *a, **k)
    )

    completar(direccion, nombres=["PEREZ QUISPE, MARIA", AJENA])

    assert guardados == []
    for modelo in apps.get_models():
        for campo in modelo._meta.concrete_fields:
            if isinstance(campo, (models.CharField, models.TextField)):
                filtro = {f"{campo.name}__icontains": "AMARANTA"}
                assert not modelo.objects.filter(**filtro).exists(), (modelo, campo.name)
    detalles = RegistroActividad.objects.values_list("detalle", flat=True)
    assert not any("AMARANTA" in str(detalle) for detalle in detalles)
