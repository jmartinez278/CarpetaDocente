"""Contexto de la pantalla y respuestas del guardado (spec competencias-periodo; design D8).

La pantalla arma, con los servicios de D3, D4, D6 y D7, el contexto que dibuja la plantilla y el
``json_script`` que lee ``competencias.js``: por periodo, número, nombre, estado, fechas,
``editable``, ``marcadas`` (``null`` sin marcas dentro del universo), ``con_notas`` y
``obligatorias``. El guardado responde 204, 400, 404 o 409. El día se fija parcheando
``timezone.localdate``.
"""

import datetime
import json
import re

import pytest
from django.test import Client
from django.urls import reverse

from actividad.tests.intentos import intentos
from institucion.models import Institucion
from notas import servicios
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import (
    AGO_1,
    COMUNICACION,
    EDUCACION_FISICA,
    INGLES,
    MAR_2,
    MATEMATICA,
    NOV_20,
    con_notas,
    ids_de,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def hoy(hoy):
    """Todas las pruebas de las vistas corren el 30 de octubre (fixture de conftest)."""
    return hoy


def marcar(seccion, periodo, ids):
    CompetenciaPeriodo.objects.bulk_create(
        CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=i) for i in ids
    )


def abrir(cliente, seccion, **parametros):
    return cliente.get(reverse("competencias:pantalla", args=[seccion.pk]), parametros)


def datos(respuesta):
    encontrado = re.search(
        r'<script id="datos-competencias" type="application/json">(.*?)</script>',
        respuesta.content.decode(),
        re.DOTALL,
    )
    assert encontrado, "la pantalla lleva el json_script de los periodos"
    return json.loads(encontrado.group(1))


def guardar(cliente, seccion, numero, ids, visto=None):
    """``visto`` es el universo que mostró la pantalla; por defecto, el de ahora."""
    if visto is None:
        visto = sorted(servicios.universo(seccion.docente, seccion))
    return cliente.post(
        reverse("competencias:guardar", args=[seccion.pk, numero]),
        {"competencia": ids, "universo": visto},
    )


# --- Contexto: áreas (spec "Competencias que ve la tutora") ---


def test_el_contexto_lleva_las_10_areas_y_el_total_marcable(cliente, seccion_tutora, ie):
    respuesta = abrir(cliente, seccion_tutora)

    areas = respuesta.context["areas"]
    assert len(areas) == 10
    assert sum(len(area.competencias) for area in areas) == 27
    assert respuesta.context["total"] == 21
    assert datos(respuesta)["total"] == 21
    assert {a.area.codigo_siagie for a in areas if a.a_cargo} == {EDUCACION_FISICA, INGLES}
    assert not any(a.marcable for a in areas if a.a_cargo)


def test_el_json_lleva_la_url_del_guardado_con_el_numero_por_cambiar(cliente, seccion_tutora, ie):
    url = datos(abrir(cliente, seccion_tutora))["url_guardar"]

    assert url == f"/docente/secciones/{seccion_tutora.pk}/competencias/0/"


def test_el_json_lleva_el_universo_que_la_pantalla_devuelve_al_guardar(cliente, seccion_tutora, ie):
    assert datos(abrir(cliente, seccion_tutora))["universo"] == sorted(ie)


# --- Periodos (spec "Periodos que se marcan") ---


def test_abre_en_el_vigente(cliente, seccion_tutora, ie):
    """Escenario "Abre en el vigente"."""
    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["periodo_inicial"].numero == 3
    assert respuesta.context["aviso"] is None
    json_ = datos(respuesta)
    assert json_["inicial"] == 3
    periodos = json_["periodos"]
    assert [p["nombre"] for p in periodos] == [
        "I bimestre",
        "II bimestre",
        "III bimestre",
        "IV bimestre",
    ]
    assert [p["corto"] for p in periodos] == ["I", "II", "III", "IV"]
    assert [p["nombre_largo"] for p in periodos] == [f"Bimestre {n}" for n in range(1, 5)]
    assert [p["estado"] for p in periodos] == ["ANTERIOR", "ANTERIOR", "VIGENTE", "FUTURO"]
    assert [p["editable"] for p in periodos] == [True, True, True, False]


def test_cada_periodo_lleva_sus_fechas(cliente, seccion_tutora, ie):
    periodos = datos(abrir(cliente, seccion_tutora))["periodos"]

    assert (periodos[2]["inicio"], periodos[2]["fin"]) == ("2027-08-10", "2027-10-30")
    assert [p["fechas"] for p in periodos] == [
        "9 mar. – 15 may.",
        "25 may. – 24 jul.",
        "10 ago. – 30 oct.",
        "8 nov. – 18 dic.",
    ]


def test_con_trimestres_los_nombres_son_t(cliente, institucion, seccion_tutora, ie):
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()

    periodos = datos(abrir(cliente, seccion_tutora))["periodos"]

    assert [p["nombre"] for p in periodos][:3] == ["I trimestre", "II trimestre", "III trimestre"]
    assert [p["corto"] for p in periodos][:3] == ["I", "II", "III"]
    assert periodos[0]["nombre_largo"] == "Trimestre 1"


def test_periodo_1_abre_el_bimestre_1(cliente, seccion_tutora, ie):
    respuesta = abrir(cliente, seccion_tutora, periodo="1")

    assert respuesta.context["periodo_inicial"].numero == 1
    assert datos(respuesta)["inicial"] == 1


@pytest.mark.parametrize("periodo", ["4", "9", "x", ""])
def test_un_periodo_que_no_se_elige_abre_el_vigente(cliente, seccion_tutora, ie, periodo):
    """``?periodo=4`` es futuro el 30 de octubre; 9 no existe; ``x`` no es un número."""
    respuesta = abrir(cliente, seccion_tutora, periodo=periodo)

    assert respuesta.context["periodo_inicial"].numero == 3
    assert datos(respuesta)["inicial"] == 3


# --- Sin periodo para marcar ---


def test_sin_periodos(cliente, seccion_tutora, universo_ie):
    """Escenario "Sin periodos"."""
    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["aviso"] == {
        "titulo": "La dirección aún no configura los periodos",
        "texto": "Cuando estén listos, podrás confirmar las competencias de tu sección.",
    }
    assert respuesta.context["periodo_inicial"] is None
    assert datos(respuesta)["periodos"] == []
    assert datos(respuesta)["inicial"] is None


def test_vacaciones(cliente, seccion_tutora, ie, hoy):
    """Escenario "Vacaciones": el 1 de agosto, entre el bimestre 2 y el 3."""
    hoy["valor"] = AGO_1

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["aviso"] == {
        "titulo": "Hoy no hay un periodo vigente",
        "texto": "Elige uno de los bimestres ya pasados para revisar sus competencias.",
    }
    assert respuesta.context["periodo_inicial"] is None
    json_ = datos(respuesta)
    assert json_["inicial"] is None
    assert [p["editable"] for p in json_["periodos"]] == [True, True, False, False]
    assert [p["estado"] for p in json_["periodos"]] == ["ANTERIOR", "ANTERIOR", "FUTURO", "FUTURO"]


def test_vacaciones_con_periodo_2_abre_el_bimestre_2(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = AGO_1

    assert abrir(cliente, seccion_tutora, periodo="2").context["periodo_inicial"].numero == 2


def test_vacaciones_en_trimestres_dice_trimestres(cliente, institucion, seccion_tutora, ie, hoy):
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()
    hoy["valor"] = AGO_1

    aviso = abrir(cliente, seccion_tutora).context["aviso"]

    assert aviso["texto"] == "Elige uno de los trimestres ya pasados para revisar sus competencias."


def test_antes_del_primer_periodo(cliente, seccion_tutora, ie, hoy):
    """Escenario "Antes del primer periodo": el 2 de marzo; el bimestre 1 empieza el 9."""
    hoy["valor"] = MAR_2

    respuesta = abrir(cliente, seccion_tutora, periodo="1")

    assert respuesta.context["aviso"] == {
        "titulo": "Hoy no hay un periodo vigente",
        "texto": "El I bimestre empieza el 9 de marzo.",
    }
    assert respuesta.context["periodo_inicial"] is None
    json_ = datos(respuesta)
    assert json_["inicial"] is None
    assert not any(p["editable"] for p in json_["periodos"])


# --- Estado inicial (spec "Estado inicial del periodo") ---


def test_un_periodo_sin_marcas_va_en_null_y_abre_con_todo_marcado(cliente, seccion_tutora, ie):
    """Escenario "Periodo sin marcas"."""
    respuesta = abrir(cliente, seccion_tutora)

    assert [p["marcadas"] for p in datos(respuesta)["periodos"]] == [None] * 4
    assert respuesta.context["marcadas_iniciales"] == ie
    assert not CompetenciaPeriodo.objects.exists()


def test_un_periodo_con_marcas_lleva_esas(cliente, seccion_tutora, bimestres, ie):
    """Escenario "Periodo con marcas": 18 de 21 en el bimestre 2."""
    dieciocho = sorted(ie)[:18]
    marcar(seccion_tutora, bimestres[1], dieciocho)

    respuesta = abrir(cliente, seccion_tutora, periodo="2")

    assert datos(respuesta)["periodos"][1]["marcadas"] == dieciocho
    assert respuesta.context["marcadas_iniciales"] == set(dieciocho)


def test_una_marca_fuera_del_universo_no_se_lee(cliente, seccion_tutora, bimestres, ie):
    """Una marca de Inglés (a cargo del docente de curso) no cuenta como marca del periodo."""
    marcar(seccion_tutora, bimestres[2], ids_de(INGLES))

    assert datos(abrir(cliente, seccion_tutora))["periodos"][2]["marcadas"] is None


def test_sin_periodo_inicial_no_hay_marcadas_iniciales(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = AGO_1

    assert abrir(cliente, seccion_tutora).context["marcadas_iniciales"] == set()


# --- Obligatorias y notas ---


def test_en_el_bimestre_4_lleva_las_obligatorias(cliente, seccion_tutora, bimestres, ie, hoy):
    """Escenario "Flujo alternativo válido": 5 sin notas en los bimestres 1 a 3."""
    faltan = sorted(ie)[:5]
    for periodo in bimestres[:3]:
        marcar(seccion_tutora, periodo, ie - set(faltan))
        con_notas(seccion_tutora, periodo, ie - set(faltan))
    hoy["valor"] = NOV_20

    respuesta = abrir(cliente, seccion_tutora)

    periodos = datos(respuesta)["periodos"]
    assert periodos[3]["obligatorias"] == faltan
    assert [p["obligatorias"] for p in periodos[:3]] == [[], [], []]
    assert respuesta.context["periodo_inicial"].numero == 4


def test_un_periodo_futuro_no_lleva_obligatorias(cliente, seccion_tutora, ie):
    """El 30 de octubre el bimestre 4 es futuro: ni obligatorias ni notas."""
    periodo_4 = datos(abrir(cliente, seccion_tutora))["periodos"][3]

    assert (periodo_4["obligatorias"], periodo_4["con_notas"]) == ([], [])


def test_sin_notas_ninguna_competencia_va_en_con_notas(cliente, seccion_tutora, ie):
    periodos = datos(abrir(cliente, seccion_tutora))["periodos"]

    assert [p["con_notas"] for p in periodos] == [[], [], [], []]


def test_con_notas_va_la_competencia_de_cada_periodo_editable(
    cliente, seccion_tutora, bimestres, ie
):
    """Escenarios «Una sola nota basta» y «Notas de otro periodo»."""
    elegida = min(ie)
    marcar(seccion_tutora, bimestres[1], [elegida])
    con_notas(seccion_tutora, bimestres[1], [elegida])

    periodos = datos(abrir(cliente, seccion_tutora))["periodos"]

    assert [p["con_notas"] for p in periodos] == [[], [elegida], [], []]


def test_las_notas_se_leen_una_vez_por_periodo_editable(cliente, seccion_tutora, ie, monkeypatch):
    """US-020 D17: el B4 futuro no se lee; los otros tres, una vez cada uno."""
    llamadas = []
    original = servicios.competencias_con_notas

    def contar(seccion, periodo):
        llamadas.append(periodo.numero)
        return original(seccion, periodo)

    monkeypatch.setattr(servicios, "competencias_con_notas", contar)

    abrir(cliente, seccion_tutora)

    assert llamadas == [1, 2, 3]


# --- Lo que la plantilla necesita (D9) ---


def test_la_palabra_del_periodo_y_los_elegibles(cliente, seccion_tutora, ie):
    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["palabra_periodo"] == "bimestre"
    assert respuesta.context["periodos_elegibles"] == "I, II y III"


def test_con_trimestres_la_palabra_es_trimestre(cliente, institucion, seccion_tutora, ie):
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["palabra_periodo"] == "trimestre"
    assert respuesta.context["periodos_elegibles"] == "I, II y III"


def test_en_vacaciones_los_elegibles_son_los_ya_pasados(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = AGO_1

    assert abrir(cliente, seccion_tutora).context["periodos_elegibles"] == "I y II"


def test_con_un_solo_elegible_va_sin_conjuncion(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = datetime.date(2027, 3, 20)

    assert abrir(cliente, seccion_tutora).context["periodos_elegibles"] == "I"


def test_sin_periodos_o_antes_del_primero_no_hay_elegibles(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = MAR_2

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["periodos_elegibles"] == ""


def test_sin_periodos_la_palabra_es_periodo(cliente, seccion_tutora, universo_ie):
    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["palabra_periodo"] == "periodo"
    assert respuesta.context["periodos_elegibles"] == ""


def test_los_bloqueos_iniciales_son_los_del_periodo_que_abre(
    cliente, seccion_tutora, bimestres, ie, hoy
):
    faltan = sorted(ie)[:5]
    for periodo in bimestres[:3]:
        marcar(seccion_tutora, periodo, ie - set(faltan))
        con_notas(seccion_tutora, periodo, ie - set(faltan))
    hoy["valor"] = NOV_20
    elegida = max(ie)
    con_notas(seccion_tutora, bimestres[3], [elegida])

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["obligatorias_iniciales"] == set(faltan)
    assert respuesta.context["con_notas_iniciales"] == {elegida}


def test_sin_periodo_inicial_no_hay_bloqueos_iniciales(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = AGO_1

    respuesta = abrir(cliente, seccion_tutora)

    assert respuesta.context["obligatorias_iniciales"] == set()
    assert respuesta.context["con_notas_iniciales"] == set()


# --- Guardado (spec "Guardar las competencias del periodo", D8) ---


def test_un_guardado_correcto_responde_204_sin_cuerpo(cliente, seccion_tutora, bimestres, ie):
    """Escenario "Camino ideal": las 7 de Matemática y Comunicación en el bimestre 3."""
    siete = sorted(ids_de(MATEMATICA, COMUNICACION))

    respuesta = guardar(cliente, seccion_tutora, 3, siete)

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert (
        sorted(
            CompetenciaPeriodo.objects.filter(periodo=bimestres[2]).values_list(
                "competencia_id", flat=True
            )
        )
        == siete
    )


def test_el_mismo_guardado_dos_veces_responde_204(cliente, seccion_tutora, bimestres, ie):
    """Escenario "Envío repetido"."""
    siete = sorted(ids_de(MATEMATICA, COMUNICACION))

    for _ in range(2):
        assert guardar(cliente, seccion_tutora, 3, siete).status_code == 204

    assert CompetenciaPeriodo.objects.count() == 7


@pytest.mark.parametrize("valor", ["x", "", "1.5"])
def test_una_competencia_que_no_es_numero_responde_400(cliente, seccion_tutora, ie, valor):
    respuesta = guardar(cliente, seccion_tutora, 3, [valor])

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": servicios.CONJUNTO_NO_VALIDO}
    assert not CompetenciaPeriodo.objects.exists()


def test_una_competencia_de_ingles_responde_400(cliente, seccion_tutora, ie):
    """Escenario "Competencia de otra área en el guardado"."""
    respuesta = guardar(cliente, seccion_tutora, 3, sorted(ids_de(MATEMATICA, INGLES)))

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "mensaje": "Las competencias enviadas no son válidas. Recarga la página."
    }
    assert not CompetenciaPeriodo.objects.exists()


def test_un_conjunto_vacio_responde_400_con_su_mensaje(cliente, seccion_tutora, ie):
    """Escenario "Conjunto vacío"."""
    respuesta = guardar(cliente, seccion_tutora, 3, [])

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": "Marca al menos una competencia para guardar."}


def test_un_numero_de_periodo_que_no_existe_responde_404(cliente, seccion_tutora, ie):
    respuesta = guardar(cliente, seccion_tutora, 9, sorted(ids_de(MATEMATICA)))

    assert respuesta.status_code == 404
    assert not CompetenciaPeriodo.objects.exists()
    assert intentos() == []


def test_un_periodo_futuro_responde_409(cliente, seccion_tutora, ie):
    """Escenario "Guardado de un periodo futuro"."""
    respuesta = guardar(cliente, seccion_tutora, 4, sorted(ids_de(MATEMATICA)))

    assert respuesta.status_code == 409
    assert respuesta.json() == {"mensaje": servicios.PERIODO_NO_MARCABLE}
    assert not CompetenciaPeriodo.objects.exists()


def test_quitar_una_competencia_con_notas_responde_409(cliente, seccion_tutora, bimestres, ie):
    """Escenario "Guardado que la quita"."""
    marcar(seccion_tutora, bimestres[2], ie)
    quitada = min(ie)
    con_notas(seccion_tutora, bimestres[2], [quitada])

    respuesta = guardar(cliente, seccion_tutora, 3, sorted(ie - {quitada}))

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "mensaje": "La competencia tiene notas registradas en este periodo",
        "competencias": [quitada],
    }
    assert CompetenciaPeriodo.objects.count() == 21


def test_un_guardado_sin_token_csrf_se_rechaza(docente, seccion_tutora, ie):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(docente)

    respuesta = guardar(cliente, seccion_tutora, 3, sorted(ids_de(MATEMATICA)))

    assert respuesta.status_code == 403
    assert not CompetenciaPeriodo.objects.exists()


def test_un_universo_distinto_al_actual_responde_400_sin_guardar(
    cliente, seccion_tutora, bimestres, ie
):
    """Escenario "Catálogo cambiado al guardar"."""
    siete = sorted(ids_de(MATEMATICA, COMUNICACION))

    respuesta = guardar(cliente, seccion_tutora, 3, siete, visto=siete)

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": servicios.CONJUNTO_NO_VALIDO}
    assert not CompetenciaPeriodo.objects.exists()


@pytest.mark.parametrize("visto", [[], ["x"]])
def test_sin_universo_o_con_uno_que_no_es_numero_responde_400(cliente, seccion_tutora, ie, visto):
    respuesta = guardar(cliente, seccion_tutora, 3, sorted(ids_de(MATEMATICA)), visto=visto)

    assert respuesta.status_code == 400
    assert respuesta.json() == {"mensaje": servicios.CONJUNTO_NO_VALIDO}
    assert not CompetenciaPeriodo.objects.exists()
