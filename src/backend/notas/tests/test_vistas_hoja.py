"""Contexto de la hoja de notas y respuestas del guardado (spec registro-notas; design D3, D8, D9).

La hoja arma con ``periodo_de_la_hoja``, ``hoja_de_notas`` y los faltantes el contexto que dibuja
la plantilla y el ``json_script`` que lee ``notas.js``. Sin marcas del periodo lleva a
Competencias. El guardado recibe un cuerpo JSON y responde 200, 400, 404 o 409 con mensajes fijos
del servicio, nunca el texto de una excepción. El día se fija con el fixture ``hoy``.
"""

import json
import re

import pytest
from django.urls import reverse

from actividad.tests.intentos import intentos
from catalogo.models import Competencia
from notas import servicios
from notas.models import Calificacion, CompetenciaPeriodo
from notas.tests.conftest import (
    AGO_1,
    COMUNICACION,
    CONCLUSION,
    INGLES,
    MAR_2,
    MATEMATICA,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)

pytestmark = pytest.mark.django_db

MENSAJES_FIJOS = {
    servicios.HOJA_CAMBIADA,
    servicios.VALOR_NO_VALIDO,
    servicios.FALTA_CONCLUSION,
    servicios.PERIODO_NO_EDITABLE,
    servicios.NOTAS_CAMBIADAS,
}


@pytest.fixture(autouse=True)
def hoy(hoy):
    return hoy


@pytest.fixture
def estudiantes(seccion_tutora):
    """Dos activos ficticios: Ana Quispe y Luis Rojas (en ese orden de apellidos)."""
    return crear_estudiantes(seccion_tutora, "QUISPE, ANA", "ROJAS, LUIS")


@pytest.fixture
def matematica(seccion_tutora, ie, bimestres, estudiantes):
    """Matemática marcada en B2 y B3 con sus 4 competencias activas."""
    for periodo in bimestres[1:3]:
        marcar(seccion_tutora, periodo, ids_de(MATEMATICA))
    return bimestres[2]


def abrir(cliente, seccion, **parametros):
    return cliente.get(reverse("notas:hoja", args=[seccion.pk]), parametros)


def datos(respuesta):
    encontrado = re.search(
        r'<script id="datos-notas" type="application/json">(.*?)</script>',
        respuesta.content.decode(),
        re.DOTALL,
    )
    assert encontrado, "la hoja lleva el json_script de las áreas"
    return json.loads(encontrado.group(1))


def area_de(dato, codigo):
    return next(area for area in dato["areas"] if area["codigo"] == codigo)


def celda(estudiante, competencia_, nivel="A", conclusion="", base=None):
    return {
        "estudiante": getattr(estudiante, "pk", estudiante),
        "competencia": getattr(competencia_, "pk", competencia_),
        "nivel": nivel,
        "conclusion": conclusion,
        "base": base,
    }


def enviar(cliente, seccion, cuerpo, numero=3, area=MATEMATICA):
    """POST del guardado; ``cuerpo`` es un objeto o un texto crudo (JSON mal formado)."""
    texto = cuerpo if isinstance(cuerpo, str) else json.dumps(cuerpo)
    return cliente.post(
        reverse("notas:guardar", args=[seccion.pk, numero, area]),
        texto,
        content_type="application/json",
    )


def guardar(cliente, seccion, *celdas, **ruta):
    return enviar(cliente, seccion, {"celdas": list(celdas)}, **ruta)


# --- Periodo de la hoja (spec "Periodo de la hoja") ---


def test_abre_en_el_vigente(cliente, seccion_tutora, matematica):
    """Escenario "Abre en el vigente"."""
    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.status_code == 200
    assert respuesta.context["periodo"].numero == 3
    assert respuesta.context["aviso"] is None
    assert datos(respuesta)["periodo"] == {
        "numero": 3,
        "nombre": "III bimestre",
        "estado": "VIGENTE",
    }


def test_el_contexto_trae_todos_los_periodos_del_anio_para_el_selector(
    cliente, seccion_tutora, matematica
):
    """Delta «Periodo de la hoja» (rebrand-us-020, D1): el selector pinta los cuatro, también el
    futuro, que no se elige."""
    respuesta = abrir(cliente, seccion_tutora)

    assert [p.numero for p in respuesta.context["periodos"]] == [1, 2, 3, 4]
    assert [p.estado for p in respuesta.context["periodos"]][-1] == "FUTURO"


def test_abre_el_periodo_anterior_pedido(cliente, seccion_tutora, matematica):
    """Escenario "Periodo anterior pedido"."""
    respuesta = abrir(cliente, seccion_tutora, periodo="2")

    assert datos(respuesta)["periodo"] == {
        "numero": 2,
        "nombre": "II bimestre",
        "estado": "ANTERIOR",
    }


@pytest.mark.parametrize("pedido", ["4", "9", "abc", ""])
def test_un_periodo_futuro_o_invalido_abre_el_vigente(cliente, seccion_tutora, matematica, pedido):
    """Escenario "Periodo futuro pedido"."""
    respuesta = abrir(cliente, seccion_tutora, periodo=pedido)

    assert datos(respuesta)["periodo"]["numero"] == 3


# --- Sin periodo vigente (spec "Sin periodo vigente") ---


def test_sin_periodos_avisa_sin_hoja(cliente, seccion_tutora, universo_ie):
    """Escenario "Sin periodos": sin json_script ni áreas."""
    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.status_code == 200
    assert respuesta.context["aviso"]["titulo"] == "La dirección aún no configura los periodos"
    assert respuesta.context["periodo"] is None
    assert "datos-notas" not in respuesta.content.decode()


def test_en_vacaciones_abre_el_ultimo_periodo_pasado(cliente, seccion_tutora, matematica, hoy):
    """Escenario "Vacaciones"."""
    hoy["valor"] = AGO_1

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["aviso"]["titulo"] == "Hoy no hay un periodo vigente"
    assert datos(respuesta)["periodo"] == {
        "numero": 2,
        "nombre": "II bimestre",
        "estado": "ANTERIOR",
    }


def test_antes_del_primer_periodo_avisa_la_fecha_sin_hoja(cliente, seccion_tutora, matematica, hoy):
    """Escenario "Antes del primer periodo"."""
    hoy["valor"] = MAR_2

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.status_code == 200
    assert respuesta.context["aviso"] == {
        "titulo": "Hoy no hay un periodo vigente",
        "texto": "El I bimestre empieza el 9 de marzo.",
    }
    assert respuesta.context["periodo"] is None
    assert "datos-notas" not in respuesta.content.decode()


# --- Periodo sin competencias marcadas (spec "Bimestre sin marcas") ---


def url_competencias(seccion, consulta):
    return f"{reverse('competencias:pantalla', args=[seccion.pk])}?{consulta}"


def test_sin_marcas_lleva_a_competencias_con_periodo_area_y_desde(
    cliente, seccion_tutora, ie, bimestres
):
    """Escenario "Bimestre sin marcas": sin ``?area=``, la primera área que marca la tutora."""
    areas = servicios.areas_de_la_seccion(seccion_tutora.docente, seccion_tutora)
    primera = next(area.area.codigo_siagie for area in areas if area.marcable)

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.status_code == 302
    assert respuesta.url == url_competencias(
        seccion_tutora, f"periodo=3&area={primera}&desde=notas"
    )


def test_sin_marcas_conserva_el_area_pedida(cliente, seccion_tutora, ie, bimestres):
    respuesta = abrir(cliente, seccion_tutora, area=MATEMATICA)

    assert respuesta.url == url_competencias(
        seccion_tutora, f"periodo=3&area={MATEMATICA}&desde=notas"
    )


def test_sin_marcas_del_periodo_pedido_lleva_a_ese_periodo(cliente, seccion_tutora, ie, bimestres):
    """Marcas en B3, ninguna en B2: «Registrar notas de B2» lleva a Competencias de B2."""
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))

    respuesta = abrir(cliente, seccion_tutora, periodo="2", area=MATEMATICA)

    assert respuesta.url == url_competencias(
        seccion_tutora, f"periodo=2&area={MATEMATICA}&desde=notas"
    )


def test_abrir_la_hoja_sin_marcas_no_guarda_marcas_ni_notas(cliente, seccion_tutora, ie, bimestres):
    abrir(cliente, seccion_tutora)

    assert not CompetenciaPeriodo.objects.exists()
    assert not Calificacion.objects.exists()


# --- Área inicial (D3) ---


@pytest.fixture
def dos_areas(seccion_tutora, matematica):
    marcar(seccion_tutora, matematica, ids_de(COMUNICACION))
    return matematica


def primera_con_columnas(dato):
    return next(area["codigo"] for area in dato["areas"] if area["columnas"])


def test_area_pedida_valida(cliente, seccion_tutora, dos_areas):
    dato = datos(abrir(cliente, seccion_tutora, area=COMUNICACION))

    assert dato["area_inicial"] == COMUNICACION


@pytest.mark.parametrize("pedida", [None, "999", ""], ids=["ausente", "invalida", "vacia"])
def test_sin_area_valida_abre_la_primera_con_columnas(cliente, seccion_tutora, dos_areas, pedida):
    parametros = {} if pedida is None else {"area": pedida}
    dato = datos(abrir(cliente, seccion_tutora, **parametros))

    assert dato["area_inicial"] == primera_con_columnas(dato)
    assert dato["area_inicial"] in {MATEMATICA, COMUNICACION}


def test_el_area_del_docente_de_curso_se_puede_pedir(cliente, seccion_tutora, dos_areas):
    """Escenario "Área del docente de curso": abre la píldora atenuada, sin celdas."""
    dato = datos(abrir(cliente, seccion_tutora, area=INGLES))

    assert dato["area_inicial"] == INGLES
    ingles = area_de(dato, INGLES)
    assert ingles["a_cargo"] is True
    assert ingles["columnas"] == [] and ingles["filas"] == [] and ingles["notas"] == {}


# --- json_script de las áreas (D2, D4, D9) ---


def test_las_areas_van_en_orden_siagie(cliente, seccion_tutora, dos_areas):
    dato = datos(abrir(cliente, seccion_tutora))

    esperadas = [
        a.area.codigo_siagie
        for a in servicios.areas_de_la_seccion(seccion_tutora.docente, seccion_tutora)
    ]
    assert [area["codigo"] for area in dato["areas"]] == esperadas


def test_el_area_lleva_columnas_filas_notas_faltantes_y_su_url(
    cliente, seccion_tutora, matematica, estudiantes, bimestres
):
    ana, luis = estudiantes
    c1, c2 = competencia(MATEMATICA, 1), competencia(MATEMATICA, 2)
    poner_nota(ana, c1, matematica, "A")
    poner_nota(luis, c2, matematica, "C")
    (mateo,) = crear_estudiantes(seccion_tutora, "TORRES, MATEO", estado="TRASLADADO")
    poner_nota(mateo, c1, matematica, "B")

    dato = datos(abrir(cliente, seccion_tutora, area=MATEMATICA))
    mate = area_de(dato, MATEMATICA)

    assert mate["nombre"] == c1.area.nombre
    assert mate["marcable"] is True and mate["a_cargo"] is False
    assert mate["total"] == 4
    assert mate["columnas"][0] == {"id": c1.pk, "etiqueta": "C1", "nombre": c1.nombre}
    assert [c["etiqueta"] for c in mate["columnas"]] == ["C1", "C2", "C3", "C4"]
    assert mate["filas"] == [
        {"id": ana.pk, "nombre": "QUISPE, ANA"},
        {"id": luis.pk, "nombre": "ROJAS, LUIS"},
    ]
    assert mate["solo_lectura"] == [
        {"id": mateo.pk, "nombre": "TORRES, MATEO", "estado": "TRASLADADO"}
    ]
    assert mate["notas"] == {
        f"{ana.pk}-{c1.pk}": {"nivel": "A", "conclusion": ""},
        f"{luis.pk}-{c2.pk}": {"nivel": "C", "conclusion": CONCLUSION},
        f"{mateo.pk}-{c1.pk}": {"nivel": "B", "conclusion": CONCLUSION},
    }
    assert mate["faltantes"] == 2 * 4 - 2, "el trasladado no cuenta"
    assert mate["url_guardar"] == reverse("notas:guardar", args=[seccion_tutora.pk, 3, MATEMATICA])


def test_el_area_marcable_sin_marcas_no_lleva_celdas(cliente, seccion_tutora, matematica):
    """Escenario "Área sin competencias marcadas"."""
    dato = datos(abrir(cliente, seccion_tutora))
    comunicacion = area_de(dato, COMUNICACION)

    assert comunicacion["marcable"] is True
    assert comunicacion["columnas"] == [] and comunicacion["filas"] == []
    assert comunicacion["faltantes"] == 0


def test_lleva_la_clave_del_borrador_sin_nombres(cliente, seccion_tutora, matematica, docente):
    dato = datos(abrir(cliente, seccion_tutora))

    assert dato["clave_borrador"] == f"cd:notas:v1:u{docente.pk}:s{seccion_tutora.pk}:p3:a"


def test_lleva_los_periodos_editables_para_nombrar_los_borradores(
    cliente, seccion_tutora, matematica
):
    """Design D11: el diálogo de salida nombra los borradores de todos los periodos que se editan;
    el bimestre 4 aún no empieza el 30 de octubre."""
    dato = datos(abrir(cliente, seccion_tutora))

    assert dato["periodos"] == [
        {"numero": 1, "nombre": "I bimestre"},
        {"numero": 2, "nombre": "II bimestre"},
        {"numero": 3, "nombre": "III bimestre"},
    ]


def test_la_hoja_lee_las_notas_en_un_numero_fijo_de_consultas(
    cliente, seccion_tutora, dos_areas, django_assert_max_num_queries
):
    with django_assert_max_num_queries(20):
        assert abrir(cliente, seccion_tutora).status_code == 200


# --- Guardado: 200 (spec "Guardar la hoja del área") ---


def test_guardar_responde_200_con_los_faltantes(cliente, seccion_tutora, matematica, estudiantes):
    """Escenario "Camino ideal (US-020)": Ana Quispe con «A» en C1 de Matemática."""
    ana, _ = estudiantes

    respuesta = guardar(cliente, seccion_tutora, celda(ana, competencia(MATEMATICA, 1)))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"faltantes": 2 * 4 - 1}
    nota = Calificacion.objects.get()
    assert (nota.estudiante, nota.nivel, nota.periodo) == (ana, "A", matematica)


def test_la_nota_guardada_vuelve_al_abrir_la_hoja(cliente, seccion_tutora, matematica, estudiantes):
    ana, _ = estudiantes
    c1 = competencia(MATEMATICA, 1)
    guardar(cliente, seccion_tutora, celda(ana, c1))

    mate = area_de(datos(abrir(cliente, seccion_tutora, area=MATEMATICA)), MATEMATICA)

    assert mate["notas"][f"{ana.pk}-{c1.pk}"] == {"nivel": "A", "conclusion": ""}


# --- Guardado: 400 ---


def sin_notas():
    return not Calificacion.objects.exists()


@pytest.mark.parametrize("nivel", ["15", "A+", ""])
def test_un_valor_fuera_de_la_escala_da_400_con_las_celdas(
    cliente, seccion_tutora, matematica, estudiantes, nivel
):
    """Escenario "Caso de error (US-022)": envío manipulado, nada se guarda."""
    ana, luis = estudiantes
    c1 = competencia(MATEMATICA, 1)

    respuesta = guardar(cliente, seccion_tutora, celda(ana, c1, "A"), celda(luis, c1, nivel))

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "mensaje": "Valor no válido. Use un nivel de la escala de calificación",
        "no_validas": [[luis.pk, c1.pk]],
        "sin_conclusion": [],
    }
    assert sin_notas()


def test_una_c_sin_conclusion_da_400_con_las_celdas(
    cliente, seccion_tutora, matematica, estudiantes
):
    """Escenario "Envío sin conclusión que llega al servidor"."""
    ana, luis = estudiantes
    c1 = competencia(MATEMATICA, 1)

    respuesta = guardar(cliente, seccion_tutora, celda(ana, c1, "A"), celda(luis, c1, "C", "Bien"))

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "mensaje": servicios.FALTA_CONCLUSION,
        "no_validas": [],
        "sin_conclusion": [[luis.pk, c1.pk]],
    }
    assert sin_notas()


def test_una_celda_de_otra_area_da_400_hoja_cambiada(
    cliente, seccion_tutora, matematica, estudiantes
):
    """Escenario "Competencia de otra área"."""
    ana, _ = estudiantes
    otra = Competencia.objects.filter(area__codigo_siagie=COMUNICACION, activa=True).first()

    respuesta = guardar(
        cliente, seccion_tutora, celda(ana, competencia(MATEMATICA, 1)), celda(ana, otra)
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": servicios.HOJA_CAMBIADA}
    assert sin_notas()


@pytest.mark.parametrize(
    "cuerpo",
    ["{no es json", "[]", "null", '"celdas"', {}, {"celdas": "x"}, {"celdas": [{"nivel": "A"}]}],
    ids=["mal-formado", "lista", "null", "texto", "sin-celdas", "celdas-texto", "celda-incompleta"],
)
def test_un_cuerpo_mal_formado_da_400_hoja_cambiada(cliente, seccion_tutora, matematica, cuerpo):
    respuesta = enviar(cliente, seccion_tutora, cuerpo)

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": servicios.HOJA_CAMBIADA}
    assert sin_notas()


def test_un_cuerpo_que_no_es_utf8_da_400(cliente, seccion_tutora, matematica):
    respuesta = cliente.post(
        reverse("notas:guardar", args=[seccion_tutora.pk, 3, MATEMATICA]),
        b"\xff\xfe\x00",
        content_type="application/json",
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": servicios.HOJA_CAMBIADA}


# --- Guardado: 404 y 409 ---


def test_un_periodo_que_no_existe_da_404(cliente, seccion_tutora, matematica, estudiantes):
    ana, _ = estudiantes

    respuesta = guardar(cliente, seccion_tutora, celda(ana, competencia(MATEMATICA, 1)), numero=9)

    assert respuesta.status_code == 404
    assert sin_notas()
    assert intentos() == []


@pytest.mark.parametrize("area", ["999", "matematica"])
def test_un_area_que_no_es_de_la_institucion_da_404(
    cliente, seccion_tutora, matematica, estudiantes, area
):
    ana, _ = estudiantes

    respuesta = guardar(cliente, seccion_tutora, celda(ana, competencia(MATEMATICA, 1)), area=area)

    assert respuesta.status_code == 404
    assert sin_notas()
    assert intentos() == []


def test_un_periodo_futuro_da_409(cliente, seccion_tutora, matematica, estudiantes, bimestres):
    """Escenario "Guardado de un periodo futuro"."""
    marcar(seccion_tutora, bimestres[3], ids_de(MATEMATICA))
    ana, _ = estudiantes

    respuesta = guardar(cliente, seccion_tutora, celda(ana, competencia(MATEMATICA, 1)), numero=4)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"mensaje": servicios.PERIODO_NO_EDITABLE}
    assert sin_notas()


def test_una_nota_cambiada_en_otro_dispositivo_da_409_con_las_celdas(
    cliente, seccion_tutora, matematica, estudiantes
):
    """Escenario "Cambio al guardar": nada se guarda y vuelve la nota de ahora."""
    ana, luis = estudiantes
    c1 = competencia(MATEMATICA, 1)
    poner_nota(ana, c1, matematica, "B")

    respuesta = guardar(cliente, seccion_tutora, celda(ana, c1, "A"), celda(luis, c1, "A"))

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "mensaje": servicios.NOTAS_CAMBIADAS,
        "cambiadas": [
            {"estudiante": ana.pk, "competencia": c1.pk, "nivel": "B", "conclusion": CONCLUSION}
        ],
    }
    assert Calificacion.objects.count() == 1


# --- Ningún cuerpo trae el texto de una excepción (lección de CodeQL en US-029) ---


def test_ninguna_respuesta_de_error_trae_el_texto_de_una_excepcion(
    cliente, seccion_tutora, matematica, estudiantes, bimestres
):
    marcar(seccion_tutora, bimestres[3], ids_de(MATEMATICA))
    ana, _ = estudiantes
    c1 = competencia(MATEMATICA, 1)
    poner_nota(ana, c1, matematica, "B")
    respuestas = [
        enviar(cliente, seccion_tutora, "{no es json"),
        guardar(cliente, seccion_tutora, celda(ana, c1, "15")),
        guardar(cliente, seccion_tutora, celda(ana, c1, "C")),
        guardar(cliente, seccion_tutora, celda(ana, c1, "A"), numero=4),
        guardar(cliente, seccion_tutora, celda(ana, c1, "A")),
        guardar(cliente, seccion_tutora, celda(ana, c1, "A"), numero=9),
        guardar(cliente, seccion_tutora, celda(ana, c1, "A"), area="999"),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code in (400, 404, 409)
        texto = respuesta.content.decode()
        for rastro in ("Traceback", "DoesNotExist", "matching query", "Expecting", "Error"):
            assert rastro not in texto
        if respuesta.status_code != 404:
            assert respuesta.json()["mensaje"] in MENSAJES_FIJOS
