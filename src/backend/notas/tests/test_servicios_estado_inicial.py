"""Estado inicial de un periodo (spec competencias-periodo, «Estado inicial del periodo»)."""

from notas import servicios


def test_sin_marcas_abre_con_todo_el_universo():
    assert servicios.estado_inicial({1, 2, 3}, None, set()) == {1, 2, 3}


def test_con_marcas_abre_con_esas():
    assert servicios.estado_inicial({1, 2, 3}, [1, 3], set()) == {1, 3}


def test_las_obligatorias_se_suman_a_lo_guardado():
    assert servicios.estado_inicial({1, 2, 3}, [1], [2]) == {1, 2}


def test_las_obligatorias_se_suman_al_universo_sin_marcas():
    assert servicios.estado_inicial({1, 2, 3}, None, [2]) == {1, 2, 3}


def test_no_cambia_el_universo_que_recibe():
    universo = {1, 2, 3}

    servicios.estado_inicial(universo, None, [2])

    assert universo == {1, 2, 3}
