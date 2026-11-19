"""Reconocer la plantilla y resolver su sección (US-024/025, design D2, D3, D5, D6).

Specs «Archivo que no corresponde a la plantilla» y «Sección de la plantilla».
"""

import pytest

from catalogo.models import Competencia
from exportaciones import servicios
from exportaciones.models import EquivalenciaSeccion
from exportaciones.tests.plantilla import CODIGO_MODULAR
from institucion.models import AnioEscolar, Institucion, Seccion
from notas.tests.conftest import MATEMATICA, competencia

pytestmark = pytest.mark.django_db


@pytest.fixture
def reconocer(direccion, ie_siagie, libro):
    def hacer(**campos):
        return servicios.reconocer(direccion, libro(**campos))

    return hacer


def guardar(seccion, nombre="TRIUNFADORES", codigo="01"):
    return EquivalenciaSeccion.objects.create(
        seccion=seccion,
        anio_escolar=seccion.anio_escolar,
        grado=seccion.grado,
        codigo_siagie=codigo,
        nombre_siagie=nombre,
    )


# --- Archivo que no corresponde a la plantilla (D2, D6) ---


def test_reconoce_la_plantilla_de_la_institucion(reconocer, ie_siagie, anio_abierto, bimestres):
    plantilla = reconocer()

    assert plantilla.institucion == ie_siagie
    assert plantilla.anio_escolar == anio_abierto
    assert plantilla.periodo == bimestres[2]
    assert plantilla.grado == 2
    assert [h.area.codigo_siagie for h in plantilla.hojas] == ["063", "0005"]


def _no_se_reconoce(hacer, **campos):
    with pytest.raises(servicios.PlantillaNoReconocida):
        hacer(**campos)


def test_otro_codigo_modular_no_se_reconoce(reconocer):
    _no_se_reconoce(reconocer, codigo_modular="0999992")


def test_otro_anexo_no_se_reconoce(reconocer, ie_siagie):
    _no_se_reconoce(reconocer, anexo=1)

    ie_siagie.anexo = 1
    ie_siagie.save()
    assert reconocer(anexo=1).institucion == ie_siagie


def test_institucion_sin_codigo_modular_no_reconoce_ninguna(reconocer, ie_siagie):
    ie_siagie.codigo_modular = None
    ie_siagie.save()

    _no_se_reconoce(reconocer)


def test_la_plantilla_de_otra_institucion_con_su_codigo_no_se_reconoce(reconocer):
    Institucion.objects.create(nombre="I.E. Ficticia N.° 3", codigo_modular="0999993")

    _no_se_reconoce(reconocer, codigo_modular="0999993")


def test_un_anio_que_la_institucion_no_tiene_no_se_reconoce(reconocer):
    _no_se_reconoce(reconocer, anio=2025)


def test_un_anio_cerrado_se_reconoce(reconocer, anio_abierto):
    anio_abierto.estado = AnioEscolar.Estado.CERRADO
    anio_abierto.save()

    assert reconocer().anio_escolar == anio_abierto


@pytest.mark.parametrize("periodo", ["B5", "B0", "T3", "3", "BB3"])
def test_un_periodo_que_no_existe_no_se_reconoce(reconocer, periodo):
    _no_se_reconoce(reconocer, periodo=periodo)


def test_un_bimestre_sin_su_periodo_creado_no_se_reconoce(reconocer, bimestres):
    bimestres[3].delete()

    _no_se_reconoce(reconocer, periodo="B4")


@pytest.mark.parametrize("organizacion", [Institucion.OrganizacionPeriodos.TRIMESTRE, None])
def test_una_institucion_que_no_es_por_bimestres_no_se_reconoce(reconocer, ie_siagie, organizacion):
    ie_siagie.organizacion_periodos = organizacion
    ie_siagie.save()

    _no_se_reconoce(reconocer)


def test_un_area_que_el_catalogo_no_tiene_no_se_reconoce(reconocer):
    _no_se_reconoce(reconocer, hojas={"063-MATE": 4, "0099-OTRA": 1})


@pytest.mark.parametrize("hojas", [{}, {"063-MATE": []}], ids=["sin-hojas", "sin-competencias"])
def test_un_libro_sin_celdas_de_notas_no_se_reconoce(reconocer, hojas):
    """Hallazgo de Codex (cierre): sin ninguna columna NL, se daba por completada sin cambios."""
    _no_se_reconoce(reconocer, hojas=hojas)


def test_la_competencia_05_en_matematica_con_4_activas_no_se_reconoce(reconocer):
    _no_se_reconoce(reconocer, hojas={"063-MATE": 5})


def test_el_numero_es_la_posicion_entre_las_activas_del_area(reconocer):
    plantilla = reconocer(hojas={"063-MATE": ["03", "01"]})

    (hoja,) = plantilla.hojas
    assert hoja.competencias == {3: competencia(MATEMATICA, 3), 1: competencia(MATEMATICA, 1)}


def test_una_competencia_desactivada_corre_los_numeros(reconocer):
    Competencia.objects.filter(pk=competencia(MATEMATICA, 1).pk).update(activa=False)

    _no_se_reconoce(reconocer, hojas={"063-MATE": 4})
    (hoja,) = reconocer(hojas={"063-MATE": 3}).hojas
    assert hoja.competencias[1] == competencia(MATEMATICA, 2)
    assert hoja.competencias[3] == competencia(MATEMATICA, 4)


def test_sin_institucion_no_se_reconoce(administrador, ie_siagie, libro):
    with pytest.raises(servicios.PlantillaNoReconocida):
        servicios.reconocer(administrador, libro())


def test_el_codigo_modular_de_la_institucion_con_espacios_igual_se_compara(reconocer, ie_siagie):
    Institucion.objects.filter(pk=ie_siagie.pk).update(codigo_modular=f" {CODIGO_MODULAR} ")

    assert reconocer().institucion == ie_siagie


# --- Sección de la plantilla (D3, D5) ---


def test_el_nombre_coincide_sin_tildes_ni_mayusculas(reconocer, anio_abierto):
    piñas = Seccion.objects.create(anio_escolar=anio_abierto, grado=2, nombre="Piñas")

    resultado = servicios.resolver_seccion(reconocer(nombre_seccion=" PINAS "))

    assert resultado == servicios.SeccionResuelta(seccion=piñas, origen=servicios.POR_NOMBRE)


def test_la_plantilla_a_con_la_seccion_a_no_pregunta(reconocer, secciones_de_segundo):
    resultado = servicios.resolver_seccion(reconocer(nombre_seccion="A"))

    assert resultado.seccion == secciones_de_segundo[0]
    assert resultado.origen == servicios.POR_NOMBRE
    assert resultado.equivalencia is None


def test_la_equivalencia_guardada_de_cualquier_periodo_manda(reconocer, secciones_de_segundo):
    equivalencia = guardar(secciones_de_segundo[1])

    resultado = servicios.resolver_seccion(reconocer(periodo="B1"))

    assert resultado.seccion == secciones_de_segundo[1]
    assert resultado.origen == servicios.POR_EQUIVALENCIA
    assert resultado.equivalencia == equivalencia


def test_la_equivalencia_es_por_codigo_y_nombre(reconocer, secciones_de_segundo):
    guardar(secciones_de_segundo[1], codigo="02")

    with pytest.raises(servicios.EligeSeccion):
        servicios.resolver_seccion(reconocer())


def test_varias_opciones_piden_elegir_sin_las_que_ya_tienen_equivalencia(
    reconocer, secciones_de_segundo, anio_abierto
):
    guardar(secciones_de_segundo[1], nombre="CAMPEONES")
    Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="A")

    with pytest.raises(servicios.EligeSeccion) as error:
        servicios.resolver_seccion(reconocer())

    a, _, c, d = secciones_de_segundo
    assert error.value.opciones == [a, c, d]
    assert error.value.plantilla.parametros.nombre_seccion == "TRIUNFADORES"


def test_sin_secciones_del_grado(reconocer, anio_abierto):
    Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="A")

    with pytest.raises(servicios.SinSeccionesDelGrado) as error:
        servicios.resolver_seccion(reconocer())

    assert str(error.value) == "Tu I.E. no tiene secciones de 2.º grado en 2027."


def test_elegir_una_de_la_lista_la_da_como_nueva(reconocer, secciones_de_segundo):
    resultado = servicios.resolver_seccion(reconocer(), secciones_de_segundo[1].pk)

    assert resultado.seccion == secciones_de_segundo[1]
    assert resultado.origen == servicios.NUEVA
    assert not EquivalenciaSeccion.objects.exists()


def test_la_seccion_elegida_llega_como_texto(reconocer, secciones_de_segundo):
    resultado = servicios.resolver_seccion(reconocer(), str(secciones_de_segundo[1].pk))

    assert resultado.seccion == secciones_de_segundo[1]


@pytest.fixture
def de_otra_institucion(otra_institucion):
    otro_anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    return Seccion.objects.create(anio_escolar=otro_anio, grado=2, nombre="B")


@pytest.fixture
def de_otro_anio(institucion):
    otro_anio = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    return Seccion.objects.create(anio_escolar=otro_anio, grado=2, nombre="B")


@pytest.mark.parametrize(
    "elegida",
    ["de_otra_institucion", "de_otro_anio", "de_tercero", "con_equivalencia", "inexistente", "x"],
)
def test_una_seccion_fuera_de_la_lista_no_es_valida(
    request, reconocer, secciones_de_segundo, anio_abierto, elegida
):
    if elegida == "de_tercero":
        seccion_id = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B").pk
    elif elegida == "con_equivalencia":
        seccion_id = guardar(secciones_de_segundo[1], nombre="CAMPEONES").seccion_id
    elif elegida == "inexistente":
        seccion_id = 999_999
    elif elegida == "x":
        seccion_id = "x"
    else:
        seccion_id = request.getfixturevalue(elegida).pk

    with pytest.raises(servicios.SeccionNoValida) as error:
        servicios.resolver_seccion(reconocer(), seccion_id)

    assert str(error.value) == "La sección elegida no es válida. Elige una de la lista."
    assert not EquivalenciaSeccion.objects.filter(nombre_siagie="TRIUNFADORES").exists()


def test_una_eleccion_distinta_de_la_equivalencia_guardada_no_es_valida(
    reconocer, secciones_de_segundo
):
    """Otra sesión guardó la equivalencia entre los dos pasos (D5)."""
    guardar(secciones_de_segundo[1])

    with pytest.raises(servicios.SeccionNoValida):
        servicios.resolver_seccion(reconocer(), secciones_de_segundo[2].pk)
    resultado = servicios.resolver_seccion(reconocer(), secciones_de_segundo[1].pk)
    assert resultado.origen == servicios.POR_EQUIVALENCIA


# --- La carrera de D5: guardar la equivalencia ---


def test_guardar_la_equivalencia_nueva_la_normaliza(reconocer, secciones_de_segundo, direccion):
    from django.db import transaction

    plantilla = reconocer(nombre_seccion="Triunfadores", codigo_seccion="03")

    with transaction.atomic():
        guardada = servicios.guardar_equivalencia(direccion, plantilla, secciones_de_segundo[1])

    assert (guardada.codigo_siagie, guardada.nombre_siagie) == ("03", "TRIUNFADORES")
    assert (guardada.anio_escolar, guardada.grado) == (plantilla.anio_escolar, 2)
    assert guardada.creado_por == direccion


def test_la_carrera_con_la_misma_seccion_sigue(reconocer, secciones_de_segundo, direccion):
    from django.db import transaction

    plantilla = reconocer()
    existente = guardar(secciones_de_segundo[1])

    with transaction.atomic():
        guardada = servicios.guardar_equivalencia(direccion, plantilla, secciones_de_segundo[1])
        # El savepoint deja la transacción usable.
        assert EquivalenciaSeccion.objects.count() == 1

    assert guardada == existente


@pytest.mark.parametrize("ocupada", ["por_el_nombre", "por_la_seccion"])
def test_la_carrera_con_otra_seccion_no_es_valida(
    reconocer, secciones_de_segundo, direccion, ocupada
):
    from django.db import transaction

    plantilla = reconocer()
    if ocupada == "por_el_nombre":
        guardar(secciones_de_segundo[2])
    else:
        guardar(secciones_de_segundo[1], nombre="CAMPEONES")

    with transaction.atomic():
        with pytest.raises(servicios.SeccionNoValida):
            servicios.guardar_equivalencia(direccion, plantilla, secciones_de_segundo[1])
        assert EquivalenciaSeccion.objects.count() == 1


@pytest.mark.parametrize("campos", [{"codigo_seccion": "12345"}, {"nombre_seccion": "N" * 61}])
def test_una_seccion_del_siagie_que_no_cabe_no_se_reconoce(reconocer, campos):
    _no_se_reconoce(reconocer, **campos)
