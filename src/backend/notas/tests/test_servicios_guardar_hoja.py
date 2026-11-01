"""Guardar la hoja de un área, todo o nada (specs registro-notas y registro-actividad; D5 a D7)."""

import pytest

from actividad.models import Operacion, RegistroActividad
from catalogo.models import InstitucionArea
from institucion.models import AnioEscolar, Estudiante, Periodo, Seccion
from notas import servicios
from notas.models import Calificacion
from notas.tests.conftest import (
    COMUNICACION,
    CONCLUSION,
    INGLES,
    MATEMATICA,
    OCT_30,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)

pytestmark = pytest.mark.django_db

OTRA_CONCLUSION = "Explica con ejemplos propios cómo resolvió el problema."


@pytest.fixture
def matematica(seccion_tutora, ie, bimestres):
    """Las 4 de Matemática y las 3 de Comunicación marcadas en el bimestre 3."""
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA, COMUNICACION))
    return [competencia(MATEMATICA, n).pk for n in (1, 2, 3, 4)]


@pytest.fixture
def lista(seccion_tutora):
    """Ana Quispe, la estudiante ficticia del criterio de US-020, y dos más."""
    return crear_estudiantes(seccion_tutora, "QUISPE, ANA", "ROJAS, MATEO", "TORRES, LUZ")


@pytest.fixture
def ana(lista):
    return lista[0]


def celda(estudiante, competencia_id, nivel, conclusion="", base=None):
    return {
        "estudiante": getattr(estudiante, "pk", estudiante),
        "competencia": competencia_id,
        "nivel": nivel,
        "conclusion": conclusion,
        "base": base,
    }


def base(nivel, conclusion=None):
    if conclusion is None:
        conclusion = CONCLUSION if nivel in ("B", "C") else ""
    return {"nivel": nivel, "conclusion": conclusion}


def guardar(docente, seccion, celdas, numero=3, area=MATEMATICA, hoy=OCT_30):
    return servicios.guardar_hoja(docente, seccion, numero, area, celdas, hoy=hoy)


def nota(estudiante, competencia_id, numero=3):
    return Calificacion.objects.get(
        estudiante=estudiante, competencia_id=competencia_id, periodo__numero=numero
    )


def entradas():
    return list(
        RegistroActividad.objects.filter(operacion=Operacion.NOTAS_GUARDADAS).order_by("id")
    )


# --- Guardar la hoja del área ---


def test_camino_ideal_guarda_la_nota_de_ana_quispe_y_deja_notas_guardadas(
    docente, seccion_tutora, bimestres, matematica, ana
):
    """Escenarios «Camino ideal (US-020)» y «Primer guardado del área»."""
    resultado = guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A")])

    guardada = nota(ana, matematica[0])
    assert (guardada.nivel, guardada.conclusion_descriptiva) == ("A", "")
    assert guardada.registrado_por == docente
    (entrada,) = entradas()
    assert (entrada.usuario, entrada.entidad, entrada.entidad_id) == (
        docente,
        "seccion",
        str(seccion_tutora.pk),
    )
    assert entrada.detalle == {"area": MATEMATICA, "periodo": 3, "creadas": 1, "cambiadas": []}
    assert (resultado.creadas, resultado.cambiadas) == (1, [])
    hoja = servicios.hoja_de_notas(docente, seccion_tutora, bimestres[2])
    de_matematica = next(h for h in hoja if h.area.codigo_siagie == MATEMATICA)
    assert de_matematica.notas[(ana.pk, matematica[0])] == ("A", "")


def test_de_b_a_a_actualiza_y_deja_el_par_cambiado_sin_niveles(
    docente, seccion_tutora, bimestres, matematica, ana
):
    """Escenarios «Flujo alternativo válido (US-020)», «De B a A» y «Corrección»."""
    anterior = poner_nota(ana, matematica[0], bimestres[2], "B")

    resultado = guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A", base=base("B"))])

    guardada = nota(ana, matematica[0])
    assert (guardada.nivel, guardada.conclusion_descriptiva) == ("A", "")
    assert guardada.actualizado_en > anterior.actualizado_en
    assert guardada.registrado_por == docente
    (entrada,) = entradas()
    assert entrada.detalle == {
        "area": MATEMATICA,
        "periodo": 3,
        "creadas": 0,
        "cambiadas": [[ana.pk, matematica[0]]],
    }
    assert (resultado.creadas, resultado.cambiadas) == (0, [(ana.pk, matematica[0])])


def test_solo_cambia_la_conclusion_lista_el_par_sin_el_texto(
    docente, seccion_tutora, bimestres, matematica, ana
):
    """Escenario «Solo cambia la conclusión»."""
    poner_nota(ana, matematica[0], bimestres[2], "C")

    guardar(
        docente,
        seccion_tutora,
        [celda(ana, matematica[0], "C", OTRA_CONCLUSION, base=base("C"))],
    )

    assert nota(ana, matematica[0]).conclusion_descriptiva == OTRA_CONCLUSION
    (entrada,) = entradas()
    assert entrada.detalle["cambiadas"] == [[ana.pk, matematica[0]]]
    assert OTRA_CONCLUSION not in str(entrada.detalle)


def test_el_envio_repetido_no_cambia_nada_ni_deja_otra_entrada(
    docente, seccion_tutora, bimestres, matematica, lista
):
    """Escenarios «Envío repetido» y «Sin cambios»."""
    celdas = [celda(e, matematica[0], "A") for e in lista]
    guardar(docente, seccion_tutora, celdas)
    antes = list(Calificacion.objects.values_list("pk", "nivel", "actualizado_en"))

    resultado = guardar(docente, seccion_tutora, celdas)

    assert list(Calificacion.objects.values_list("pk", "nivel", "actualizado_en")) == antes
    assert len(entradas()) == 1
    assert (resultado.creadas, resultado.cambiadas) == (0, [])


def test_guardar_sin_celdas_no_deja_entrada(docente, seccion_tutora, bimestres, matematica, lista):
    resultado = guardar(docente, seccion_tutora, [])

    assert not entradas()
    assert resultado.faltantes == 12


def test_con_celdas_vacias_guarda_las_demas_y_cuenta_las_faltantes(
    docente, seccion_tutora, bimestres, matematica, lista
):
    """Escenario «Guardar con celdas vacías»: 3 estudiantes × 4 competencias, 6 sin nivel."""
    celdas = [celda(e, c, "AD") for e in lista for c in matematica[:2]]

    resultado = guardar(docente, seccion_tutora, celdas)

    assert Calificacion.objects.count() == 6
    assert resultado.faltantes == 6


# --- Conclusión en B y C ---


def test_c_con_conclusion_guarda_el_nivel_y_la_conclusion(
    docente, seccion_tutora, bimestres, matematica, ana
):
    """Escenario «Camino ideal (US-021)»; la conclusión se guarda sin espacios alrededor."""
    guardar(docente, seccion_tutora, [celda(ana, matematica[0], "C", f"  {CONCLUSION}  ")])

    guardada = nota(ana, matematica[0])
    assert (guardada.nivel, guardada.conclusion_descriptiva) == ("C", CONCLUSION)


def test_c_con_diez_caracteres_se_guarda(docente, seccion_tutora, bimestres, matematica, ana):
    guardar(docente, seccion_tutora, [celda(ana, matematica[0], "C", "x" * 10)])

    assert nota(ana, matematica[0]).conclusion_descriptiva == "x" * 10


def test_a_con_conclusion_la_guarda_vacia(docente, seccion_tutora, bimestres, matematica, ana):
    guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A", CONCLUSION)])

    assert nota(ana, matematica[0]).conclusion_descriptiva == ""


@pytest.mark.parametrize(
    ("nivel", "conclusion"),
    [("C", ""), ("C", "   "), ("B", "Bien"), ("B", "x" * 9), ("C", "x" * 501)],
)
def test_conclusion_faltante_o_corta_no_guarda_nada(
    docente, seccion_tutora, bimestres, matematica, lista, nivel, conclusion
):
    """Escenarios «Caso de error (US-021)», «Conclusión corta en B» y «Envío sin conclusión»."""
    ana, mateo, _ = lista
    celdas = [celda(mateo, matematica[0], "A"), celda(ana, matematica[1], nivel, conclusion)]

    with pytest.raises(servicios.HojaConErrores) as error:
        guardar(docente, seccion_tutora, celdas)

    assert error.value.sin_conclusion == [(ana.pk, matematica[1])]
    assert error.value.no_validas == []
    assert str(error.value) == servicios.FALTA_CONCLUSION
    assert not Calificacion.objects.exists()
    assert not entradas()


# --- Valor fuera de la escala ---


@pytest.mark.parametrize("nivel", ["15", "A+", "", "  ", "D", "a d"])
def test_un_valor_fuera_de_la_escala_no_guarda_nada(
    docente, seccion_tutora, bimestres, matematica, lista, nivel
):
    """Escenario «Caso de error (US-022)»."""
    ana, mateo, _ = lista
    celdas = [celda(mateo, matematica[0], "A"), celda(ana, matematica[0], nivel)]

    with pytest.raises(servicios.HojaConErrores) as error:
        guardar(docente, seccion_tutora, celdas)

    assert error.value.no_validas == [(ana.pk, matematica[0])]
    assert str(error.value) == "Valor no válido. Use un nivel de la escala de calificación"
    assert not Calificacion.objects.exists()


def test_con_valor_no_valido_y_conclusion_faltante_manda_el_de_la_escala(
    docente, seccion_tutora, bimestres, matematica, lista
):
    ana, mateo, _ = lista
    celdas = [celda(mateo, matematica[0], "C"), celda(ana, matematica[0], "15")]

    with pytest.raises(servicios.HojaConErrores) as error:
        guardar(docente, seccion_tutora, celdas)

    assert error.value.no_validas == [(ana.pk, matematica[0])]
    assert error.value.sin_conclusion == [(mateo.pk, matematica[0])]
    assert str(error.value) == servicios.VALOR_NO_VALIDO


@pytest.mark.parametrize(("enviado", "guardado"), [(" ad ", "AD"), ("b", "B"), ("A", "A")])
def test_minusculas_y_espacios(
    docente, seccion_tutora, bimestres, matematica, ana, enviado, guardado
):
    """Escenarios «Camino ideal (US-022)» y «Minúsculas y espacios»."""
    guardar(docente, seccion_tutora, [celda(ana, matematica[0], enviado, CONCLUSION)])

    assert nota(ana, matematica[0]).nivel == guardado


def test_una_nota_no_vuelve_a_vacia(docente, seccion_tutora, bimestres, matematica, ana):
    """Escenario «Una nota no vuelve a vacía» (RN-023): el servidor nunca borra una nota."""
    poner_nota(ana, matematica[0], bimestres[2], "A")

    with pytest.raises(servicios.HojaConErrores) as error:
        guardar(docente, seccion_tutora, [celda(ana, matematica[0], "", base=base("A"))])

    assert error.value.no_validas == [(ana.pk, matematica[0])]
    assert nota(ana, matematica[0]).nivel == "A"


# --- Celdas fuera de la hoja ---


def test_estudiante_trasladado_con_la_hoja_abierta(
    docente, seccion_tutora, bimestres, matematica, lista
):
    """Escenario «Estudiante trasladado con la hoja abierta»."""
    ana, mateo, _ = lista
    Estudiante.objects.filter(pk=mateo.pk).update(estado=Estudiante.Estado.TRASLADADO)

    with pytest.raises(servicios.HojaCambiada) as error:
        guardar(
            docente,
            seccion_tutora,
            [celda(ana, matematica[0], "A"), celda(mateo, matematica[0], "A")],
        )

    assert str(error.value) == "La hoja cambió desde que la abriste. Recarga la página."
    assert not Calificacion.objects.exists()


def test_competencia_de_otra_area(docente, seccion_tutora, bimestres, matematica, ana):
    """Escenario «Competencia de otra área»."""
    de_comunicacion = competencia(COMUNICACION, 1).pk

    with pytest.raises(servicios.HojaCambiada):
        guardar(
            docente,
            seccion_tutora,
            [celda(ana, matematica[0], "A"), celda(ana, de_comunicacion, "A")],
        )

    assert not Calificacion.objects.exists()


def test_competencia_no_marcada_en_el_periodo(docente, seccion_tutora, bimestres, ie, ana):
    marcar(seccion_tutora, bimestres[2], [competencia(MATEMATICA, 1).pk])

    with pytest.raises(servicios.HojaCambiada):
        guardar(docente, seccion_tutora, [celda(ana, competencia(MATEMATICA, 2).pk, "A")])


def test_competencia_marcada_pero_desactivada(docente, seccion_tutora, bimestres, matematica, ana):
    desactivada = competencia(MATEMATICA, 1)
    desactivada.activa = False
    desactivada.save()

    with pytest.raises(servicios.HojaCambiada):
        guardar(docente, seccion_tutora, [celda(ana, desactivada.pk, "A")])


def test_area_del_docente_de_curso(docente, seccion_tutora, bimestres, ie, ana):
    de_ingles = ids_de(INGLES)
    marcar(seccion_tutora, bimestres[2], de_ingles)

    with pytest.raises(servicios.HojaCambiada):
        guardar(docente, seccion_tutora, [celda(ana, min(de_ingles), "A")], area=INGLES)

    assert not Calificacion.objects.exists()


def test_estudiante_de_otra_seccion(
    docente, seccion_tutora, bimestres, matematica, ana, anio_abierto
):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B")
    ajeno = crear_estudiantes(otra, "MAMANI, SOFÍA")[0]

    with pytest.raises(servicios.HojaCambiada):
        guardar(docente, seccion_tutora, [celda(ajeno, matematica[0], "A")])


def test_celda_repetida(docente, seccion_tutora, bimestres, matematica, ana):
    with pytest.raises(servicios.HojaCambiada):
        guardar(
            docente,
            seccion_tutora,
            [celda(ana, matematica[0], "A"), celda(ana, matematica[0], "AD")],
        )

    assert not Calificacion.objects.exists()


@pytest.mark.parametrize(
    "mala",
    [
        "texto",
        None,
        {"estudiante": "1", "competencia": 1, "nivel": "A", "conclusion": "", "base": None},
        {"estudiante": True, "competencia": 1, "nivel": "A", "conclusion": "", "base": None},
        {"estudiante": 1, "competencia": 1, "nivel": 5, "conclusion": "", "base": None},
        {"estudiante": 1, "competencia": 1, "nivel": "A", "conclusion": None, "base": None},
        {"estudiante": 1, "competencia": 1, "nivel": "A", "conclusion": "", "base": "A"},
        {"estudiante": 1, "competencia": 1, "nivel": "A", "conclusion": "", "base": {"n": 1}},
        {"estudiante": 1, "competencia": 1, "nivel": "A"},
    ],
)
def test_una_celda_mal_formada(docente, seccion_tutora, bimestres, matematica, ana, mala):
    with pytest.raises(servicios.HojaCambiada):
        guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A"), mala])

    assert not Calificacion.objects.exists()


def test_celdas_que_no_son_una_lista(docente, seccion_tutora, bimestres, matematica):
    with pytest.raises(servicios.HojaCambiada):
        guardar(docente, seccion_tutora, {"celdas": []})


# --- Periodo y área ---


def test_un_periodo_futuro_no_se_guarda(docente, seccion_tutora, bimestres, ie, ana):
    """Escenario «Guardado de un periodo futuro»."""
    marcar(seccion_tutora, bimestres[3], ids_de(MATEMATICA))

    with pytest.raises(servicios.PeriodoNoEditable) as error:
        guardar(
            docente,
            seccion_tutora,
            [celda(ana, competencia(MATEMATICA, 1).pk, "A")],
            numero=4,
        )

    assert str(error.value) == servicios.PERIODO_NO_EDITABLE
    assert not Calificacion.objects.exists()


def test_un_anio_cerrado_no_se_guarda(
    docente, seccion_tutora, bimestres, matematica, ana, anio_abierto
):
    AnioEscolar.objects.filter(pk=anio_abierto.pk).update(estado=AnioEscolar.Estado.CERRADO)

    with pytest.raises(servicios.PeriodoNoEditable):
        guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A")])

    assert not Calificacion.objects.exists()


def test_un_periodo_que_no_existe(docente, seccion_tutora, bimestres, matematica, ana):
    with pytest.raises(Periodo.DoesNotExist):
        guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A")], numero=9)


@pytest.mark.parametrize("codigo", ["9999", "0002"])
def test_un_area_que_la_institucion_no_trabaja(
    docente, seccion_tutora, bimestres, matematica, ana, codigo
):
    """«9999» no existe; Castellano (0002) no se trabaja en la I.E."""
    with pytest.raises(InstitucionArea.DoesNotExist):
        guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A")], area=codigo)


# --- Nota cambiada desde otro dispositivo (D6, D7) ---


def test_una_base_distinta_no_guarda_nada_y_trae_la_nota_actual(
    docente, seccion_tutora, bimestres, matematica, lista
):
    """Escenario «Cambio al guardar»: la laptop vio «A»; el celular guardó «AD»."""
    ana, mateo, _ = lista
    poner_nota(ana, matematica[0], bimestres[2], "AD")
    celdas = [
        celda(ana, matematica[0], "B", CONCLUSION, base=base("A")),
        celda(mateo, matematica[0], "A"),
    ]

    with pytest.raises(servicios.NotasCambiadas) as error:
        guardar(docente, seccion_tutora, celdas)

    assert error.value.cambiadas == [
        {"estudiante": ana.pk, "competencia": matematica[0], "nivel": "AD", "conclusion": ""}
    ]
    assert str(error.value) == servicios.NOTAS_CAMBIADAS
    assert nota(ana, matematica[0]).nivel == "AD"
    assert Calificacion.objects.count() == 1
    assert not entradas()


def test_tras_el_choque_el_segundo_guardado_con_la_base_nueva_guarda(
    docente, seccion_tutora, bimestres, matematica, ana
):
    poner_nota(ana, matematica[0], bimestres[2], "AD")

    guardar(
        docente,
        seccion_tutora,
        [celda(ana, matematica[0], "B", CONCLUSION, base=base("AD"))],
    )

    assert nota(ana, matematica[0]).nivel == "B"


def test_una_nota_creada_en_otro_dispositivo_sobre_una_celda_vacia_es_un_choque(
    docente, seccion_tutora, bimestres, matematica, ana
):
    poner_nota(ana, matematica[0], bimestres[2], "C", OTRA_CONCLUSION)

    with pytest.raises(servicios.NotasCambiadas) as error:
        guardar(docente, seccion_tutora, [celda(ana, matematica[0], "A")])

    assert error.value.cambiadas == [
        {
            "estudiante": ana.pk,
            "competencia": matematica[0],
            "nivel": "C",
            "conclusion": OTRA_CONCLUSION,
        }
    ]


def test_una_base_distinta_con_la_actual_igual_a_la_enviada_no_es_un_choque(
    docente, seccion_tutora, bimestres, matematica, ana
):
    """D6: la nota ya es la enviada; no se escribe ni deja entrada."""
    poner_nota(ana, matematica[0], bimestres[2], "AD")

    resultado = guardar(docente, seccion_tutora, [celda(ana, matematica[0], "ad", base=base("A"))])

    assert (resultado.creadas, resultado.cambiadas) == (0, [])
    assert not entradas()


def test_nada_cambio_en_otro_lado_guarda_sin_avisos(
    docente, seccion_tutora, bimestres, matematica, ana
):
    """Escenario «Nada cambió en otro lado»."""
    poner_nota(ana, matematica[0], bimestres[2], "B")

    resultado = guardar(docente, seccion_tutora, [celda(ana, matematica[0], "AD", base=base("B"))])

    assert resultado.cambiadas == [(ana.pk, matematica[0])]


# --- Todo o nada (RNF-011) ---


def test_una_escritura_que_falla_a_mitad_no_deja_notas_ni_entrada(
    docente, seccion_tutora, bimestres, matematica, lista, monkeypatch
):
    ana, mateo, _ = lista
    poner_nota(ana, matematica[0], bimestres[2], "B")

    def falla(*args, **kwargs):
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(servicios, "registrar", falla)

    with pytest.raises(RuntimeError):
        guardar(
            docente,
            seccion_tutora,
            [
                celda(ana, matematica[0], "A", base=base("B")),
                celda(mateo, matematica[0], "AD"),
            ],
        )

    assert nota(ana, matematica[0]).nivel == "B"
    assert Calificacion.objects.count() == 1
    assert not RegistroActividad.objects.exists()


def test_el_resultado_trae_las_faltantes_del_area(
    docente, seccion_tutora, bimestres, matematica, lista
):
    resultado = guardar(docente, seccion_tutora, [celda(lista[0], matematica[0], "A")])

    assert resultado.faltantes == 11
