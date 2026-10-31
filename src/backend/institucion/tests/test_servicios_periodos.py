"""Reglas y guardado de los periodos (spec periodos-anio-escolar; design de US-028, D2, D4 y D6)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from actividad.models import Operacion, RegistroActividad
from institucion import servicios
from institucion.models import AnioEscolar, Institucion, Periodo

pytestmark = pytest.mark.django_db

BIMESTRES = [
    (1, (16, 3), (15, 5)),
    (2, (25, 5), (24, 7)),
    (3, (10, 8), (9, 10)),
    (4, (19, 10), (18, 12)),
]


def _fecha(dia, mes, anio=2027):
    return datetime.date(anio, mes, dia)


def _filas(tabla=BIMESTRES, anio=2027):
    return [(n, _fecha(*inicio, anio), _fecha(*fin, anio)) for n, inicio, fin in tabla]


def _con(filas, numero, inicio=None, fin=None):
    """Las filas con las fechas de ``numero`` cambiadas."""
    return [(n, inicio or i, fin or f) if n == numero else (n, i, f) for n, i, f in filas]


def _errores_por_fila(error):
    return {numero: mensajes for numero, mensajes in error.value.message_dict.items()}


@pytest.fixture
def anio(anio_abierto):
    """El año 2027 ABIERTO de una institución organizada en bimestres."""
    institucion = anio_abierto.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    return anio_abierto


@pytest.fixture
def configurado(anio, administrador):
    servicios.guardar_periodos(anio, _filas(), administrador)
    return anio


# --- validar_periodos (D2) ---


def test_filas_validas_pasan(anio):
    servicios.validar_periodos(anio, _filas())


def test_hueco_de_vacaciones_es_valido(anio):
    servicios.validar_periodos(anio, _con(_filas(), 3, inicio=_fecha(10, 8)))


def test_todas_vacias_es_valido(anio):
    servicios.validar_periodos(anio, [(n, None, None) for n in range(1, 5)])


@pytest.mark.parametrize("fin", [_fecha(16, 3), _fecha(10, 3)], ids=["igual", "anterior"])
def test_fin_no_posterior_al_inicio_en_su_fila(anio, fin):
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, _con(_filas(), 1, fin=fin))

    assert _errores_por_fila(error) == {1: ["La fecha de fin debe ser posterior a la de inicio."]}


@pytest.mark.parametrize(
    "fin", [_fecha(5, 1, 2028), _fecha(1, 1, 2028)], ids=["5-enero", "1-enero"]
)
def test_fuera_del_anio_en_su_fila(anio, fin):
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, _con(_filas(), 4, fin=fin))

    assert _errores_por_fila(error) == {4: ["Las fechas deben estar dentro de 2027."]}


def test_inicio_en_el_anio_anterior_esta_fuera(anio):
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, _con(_filas(), 1, inicio=_fecha(31, 12, 2026)))

    assert _errores_por_fila(error) == {1: ["Las fechas deben estar dentro de 2027."]}


@pytest.mark.parametrize("vacio", ["inicio", "fin", "ambas"])
def test_filas_incompletas_dicen_cuantas_completar(anio, vacio):
    filas = _filas()
    n, inicio, fin = filas[3]
    filas[3] = (
        n,
        None if vacio in ("inicio", "ambas") else inicio,
        None if vacio in ("fin", "ambas") else fin,
    )

    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, filas)

    assert error.value.messages == ["Completa las fechas de los 4 periodos."]


@pytest.mark.parametrize("inicio", [_fecha(1, 5), _fecha(15, 5)], ids=["dentro", "mismo-dia"])
def test_cruce_en_la_fila_de_numero_mayor(anio, inicio):
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, _con(_filas(), 2, inicio=inicio))

    assert _errores_por_fila(error) == {2: ["Las fechas se cruzan con otro periodo"]}
    assert servicios.MENSAJE_CRUCE == "Las fechas se cruzan con otro periodo"


def test_cruce_entre_periodos_no_vecinos(anio):
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, _con(_filas(), 4, inicio=_fecha(1, 10)))

    assert _errores_por_fila(error) == {4: [servicios.MENSAJE_CRUCE]}


def test_fuera_de_orden_en_la_fila_siguiente(anio):
    filas = _filas(
        [(1, (1, 6), (31, 7)), (2, (1, 3), (15, 5)), (3, (10, 8), (9, 10)), (4, (19, 10), (18, 12))]
    )

    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, filas)

    assert _errores_por_fila(error) == {
        2: ["El periodo 2 debe empezar después de que termina el periodo 1."]
    }


def test_cruce_y_desorden_a_la_vez_da_el_mensaje_del_cruce(anio):
    # El 2 empieza antes que el 1 y además se cruzan.
    filas = _con(_filas(), 2, inicio=_fecha(1, 3), fin=_fecha(20, 3))

    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, filas)

    assert _errores_por_fila(error) == {2: [servicios.MENSAJE_CRUCE]}


def test_trimestres_son_tres_filas(anio):
    institucion = anio.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()
    trimestres = [(1, (16, 3), (31, 5)), (2, (10, 6), (31, 8)), (3, (10, 9), (18, 12))]

    servicios.validar_periodos(anio, _filas(trimestres))
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, [*_filas(trimestres)[:2], (3, None, None)])

    assert error.value.messages == ["Completa las fechas de los 3 periodos."]


def test_anio_cerrado_se_rechaza(anio):
    anio.estado = AnioEscolar.Estado.CERRADO

    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio, _filas())

    assert error.value.messages == ["El año escolar está cerrado: sus periodos no cambian."]


def test_organizacion_vacia_se_rechaza(anio_abierto):
    with pytest.raises(ValidationError) as error:
        servicios.validar_periodos(anio_abierto, _filas())

    assert error.value.messages == [
        "Define la organización de periodos de la institución antes de configurar sus periodos."
    ]


# --- guardar_periodos (D4, D6) ---


def test_guardar_crea_los_periodos_y_deja_periodos_configurados(anio, administrador):
    cambios = servicios.guardar_periodos(anio, _filas(), administrador)

    periodos = list(anio.periodos.values_list("numero", "fecha_inicio", "fecha_fin"))
    assert periodos == _filas()
    assert [p.numero for p in cambios.creados] == [1, 2, 3, 4]
    assert cambios.editados == []
    entrada = RegistroActividad.objects.get(operacion=Operacion.PERIODOS_CONFIGURADOS)
    assert (entrada.usuario, entrada.entidad, entrada.entidad_id, entrada.detalle) == (
        administrador,
        "anio_escolar",
        str(anio.pk),
        {"periodos": 4},
    )
    assert not RegistroActividad.objects.filter(operacion=Operacion.PERIODO_EDITADO).exists()


def test_editar_dos_periodos_deja_dos_periodo_editado_sin_cambiar_sus_id(
    configurado, administrador
):
    """Escenario "Flujo alternativo válido": el id del periodo no cambia (las notas lo usan)."""
    ids = dict(configurado.periodos.values_list("numero", "id"))
    filas = _con(_con(_filas(), 1, fin=_fecha(20, 5)), 2, inicio=_fecha(1, 6))

    cambios = servicios.guardar_periodos(configurado, filas, administrador)

    assert dict(configurado.periodos.values_list("numero", "id")) == ids
    assert list(configurado.periodos.values_list("numero", "fecha_inicio", "fecha_fin")) == filas
    assert cambios.creados == []
    entradas = RegistroActividad.objects.filter(operacion=Operacion.PERIODO_EDITADO).order_by("id")
    assert [(e.usuario, e.entidad, e.entidad_id, e.detalle) for e in entradas] == [
        (
            administrador,
            "periodo",
            str(ids[1]),
            {
                "numero": 1,
                "inicio_antes": "2027-03-16",
                "fin_antes": "2027-05-15",
                "inicio_despues": "2027-03-16",
                "fin_despues": "2027-05-20",
            },
        ),
        (
            administrador,
            "periodo",
            str(ids[2]),
            {
                "numero": 2,
                "inicio_antes": "2027-05-25",
                "fin_antes": "2027-07-24",
                "inicio_despues": "2027-06-01",
                "fin_despues": "2027-07-24",
            },
        ),
    ]
    assert RegistroActividad.objects.filter(operacion=Operacion.PERIODOS_CONFIGURADOS).count() == 1


def test_guardar_sin_cambios_no_deja_entradas(configurado, administrador):
    antes = RegistroActividad.objects.count()

    cambios = servicios.guardar_periodos(configurado, _filas(), administrador)

    assert (cambios.creados, cambios.editados) == ([], [])
    assert RegistroActividad.objects.count() == antes


def test_guardar_todas_vacias_no_crea_nada(anio, administrador):
    servicios.guardar_periodos(anio, [(n, None, None) for n in range(1, 5)], administrador)

    assert not Periodo.objects.exists()
    assert not RegistroActividad.objects.exists()


def test_vaciar_las_filas_de_un_anio_con_periodos_se_rechaza(configurado, administrador):
    with pytest.raises(ValidationError) as error:
        servicios.guardar_periodos(
            configurado, [(n, None, None) for n in range(1, 5)], administrador
        )

    assert error.value.messages == ["Completa las fechas de los 4 periodos."]
    assert configurado.periodos.count() == 4


def test_correr_el_fin_del_1_y_el_inicio_del_2_a_la_vez_se_guarda(configurado, administrador):
    """Escenario "Correr dos periodos a la vez": el fin nuevo del 1 cruza el inicio viejo del 2."""
    filas = _con(_con(_filas(), 1, fin=_fecha(31, 5)), 2, inicio=_fecha(8, 6))

    servicios.guardar_periodos(configurado, filas, administrador)

    assert list(configurado.periodos.values_list("numero", "fecha_inicio", "fecha_fin")) == filas


def test_cruce_que_solo_ve_la_base_da_el_mensaje_sin_guardar_nada(anio, administrador, monkeypatch):
    """Escenario "Cruce que llega a la base": la validación no lo vio; la base sí."""
    monkeypatch.setattr(servicios, "validar_periodos", lambda anio, filas: None)
    filas = _con(_filas(), 2, inicio=_fecha(15, 5))

    with pytest.raises(ValidationError) as error:
        servicios.guardar_periodos(anio, filas, administrador)

    assert error.value.messages == [servicios.MENSAJE_CRUCE]
    assert not Periodo.objects.exists()
    assert not RegistroActividad.objects.exists()


def test_rechazado_por_cruce_no_deja_entradas(configurado, administrador):
    """Escenario "Rechazado" del registro de actividad."""
    antes = RegistroActividad.objects.count()

    with pytest.raises(ValidationError):
        servicios.guardar_periodos(
            configurado, _con(_filas(), 2, inicio=_fecha(10, 5)), administrador
        )

    assert RegistroActividad.objects.count() == antes
    assert list(configurado.periodos.values_list("numero", "fecha_inicio", "fecha_fin")) == _filas()


def test_guardar_usa_el_anio_de_la_base_y_no_una_copia_vieja(configurado, administrador):
    copia = AnioEscolar.objects.get(pk=configurado.pk)
    AnioEscolar.objects.filter(pk=configurado.pk).update(estado=AnioEscolar.Estado.CERRADO)

    with pytest.raises(ValidationError):
        servicios.guardar_periodos(copia, _con(_filas(), 1, fin=_fecha(20, 5)), administrador)

    assert configurado.periodos.get(numero=1).fecha_fin == _fecha(15, 5)


# --- Organización fija con periodos (D5) ---


def test_cambiar_la_organizacion_con_periodos_guardados_se_rechaza(configurado):
    institucion = Institucion.objects.get(pk=configurado.institucion_id)
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE

    with pytest.raises(ValidationError) as error:
        servicios.validar_organizacion(institucion)

    assert error.value.message_dict == {"organizacion_periodos": [servicios.ORGANIZACION_FIJA]}


def test_vaciar_la_organizacion_con_periodos_guardados_se_rechaza(configurado):
    institucion = Institucion.objects.get(pk=configurado.institucion_id)
    institucion.organizacion_periodos = None

    with pytest.raises(ValidationError):
        servicios.validar_organizacion(institucion)


def test_la_organizacion_cambia_si_no_hay_periodos(anio):
    institucion = anio.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE

    servicios.validar_organizacion(institucion)


def test_la_misma_organizacion_con_periodos_pasa(configurado):
    servicios.validar_organizacion(Institucion.objects.get(pk=configurado.institucion_id))


def test_una_institucion_nueva_pasa(db):
    servicios.validar_organizacion(Institucion(nombre="I.E. Ficticia N.° 3"))
