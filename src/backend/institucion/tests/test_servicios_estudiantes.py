"""Pruebas de los servicios de la lista de estudiantes (spec estudiantes-seccion; D2 y D9)."""

import pytest
from django.core.exceptions import ValidationError
from django.db.models import RestrictedError
from django.db.models.query import QuerySet

from institucion import servicios
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.django_db

HOMONIMO = "Este estudiante ya está en la lista"


def texto_de(cantidad):
    return "\n".join(f"APELLIDO{i:02d} FICTICIO, NOMBRE{i:02d}" for i in range(cantidad))


def crear(seccion, *nombres):
    """Crea estudiantes a partir de textos "APELLIDOS, NOMBRES"."""
    for nombre in nombres:
        apellidos, nombres_ = nombre.split(", ")
        Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres=nombres_)


def titulos(errores):
    return [error.titulo for error in errores]


# --- importar_lista ---


def test_25_lineas_validas_crean_25_estudiantes(seccion):
    cantidad, errores = servicios.importar_lista(seccion, texto_de(25))

    assert (cantidad, errores) == (25, [])
    assert seccion.estudiantes.count() == 25


def test_las_lineas_en_blanco_no_dan_error(seccion):
    texto = "\n\n".join(texto_de(25).split("\n")) + "\n\n"

    cantidad, errores = servicios.importar_lista(seccion, texto)

    assert (cantidad, errores) == (25, [])


def test_con_un_error_no_se_guarda_ninguno(seccion):
    texto = texto_de(24) + "\nCONDORI MAMANI DANIELA"

    cantidad, errores = servicios.importar_lista(seccion, texto)

    assert cantidad == 0
    assert titulos(errores) == ["Línea 25: falta la coma entre apellidos y nombres"]
    assert seccion.estudiantes.count() == 0


def test_121_caracteres_en_apellidos(seccion):
    texto = texto_de(14) + "\n" + "A" * 121 + ", ANA"

    cantidad, errores = servicios.importar_lista(seccion, texto)

    assert cantidad == 0
    assert titulos(errores) == ["Línea 15: los apellidos tienen más de 120 caracteres"]
    assert errores[0].ayuda == "Usa un máximo de 120 caracteres por campo, sin datos adicionales."


def test_121_caracteres_en_nombres(seccion):
    _, errores = servicios.importar_lista(seccion, "QUISPE, " + "A" * 121)

    assert titulos(errores) == ["Línea 1: los nombres tienen más de 120 caracteres"]


def test_120_caracteres_se_aceptan(seccion):
    cantidad, errores = servicios.importar_lista(seccion, "A" * 120 + ", " + "B" * 120)

    assert (cantidad, errores) == (1, [])


def test_el_largo_se_mide_despues_de_normalizar(seccion):
    cantidad, _ = servicios.importar_lista(seccion, "A" * 100 + " " * 50 + "B" * 15 + ", ANA")

    assert cantidad == 1


def test_repetidos_se_agrupan_en_un_error(seccion):
    lineas = [f"APELLIDO{i}, NOMBRE{i}" for i in range(12)]
    lineas[3] = "QUISPE MAMANI, ANA"
    lineas[11] = "quispe  mamani ,  ana"

    cantidad, errores = servicios.importar_lista(seccion, "\n".join(lineas))

    assert cantidad == 0
    assert titulos(errores) == ["Líneas 4 y 12: el mismo estudiante"]
    assert errores[0].ayuda == (
        "Deja una sola línea. Si son personas distintas, escribe el segundo nombre completo."
    )


def test_tres_repetidos_se_listan_con_comas_y_una_y(seccion):
    lineas = [f"APELLIDO{i}, NOMBRE{i}" for i in range(12)]
    for numero in (4, 9, 12):
        lineas[numero - 1] = "Quispe Mamani, Ana"

    _, errores = servicios.importar_lista(seccion, "\n".join(lineas))

    assert titulos(errores) == ["Líneas 4, 9 y 12: el mismo estudiante"]


def test_jose_y_jose_con_tilde_son_dos_estudiantes(seccion):
    cantidad, errores = servicios.importar_lista(seccion, "RAMOS, JOSE\nRAMOS, JOSÉ")

    assert (cantidad, errores) == (2, [])


def test_los_errores_van_por_orden_de_linea(seccion):
    texto = "A, B\nA, B\nSIN COMA\nC, D\nC, D"

    _, errores = servicios.importar_lista(seccion, texto)

    assert titulos(errores) == [
        "Líneas 1 y 2: el mismo estudiante",
        "Línea 3: falta la coma entre apellidos y nombres",
        "Líneas 4 y 5: el mismo estudiante",
    ]


def test_texto_vacio_pide_pegar_al_menos_un_estudiante(seccion):
    cantidad, errores = servicios.importar_lista(seccion, "\n  \n")

    assert cantidad == 0
    assert titulos(errores) == ["Pega al menos un estudiante"]
    assert errores[0].ayuda == "Copia la columna de apellidos y nombres de tu Excel y pégala aquí"


def test_mas_de_60_lineas_no_guarda_nada(seccion):
    cantidad, errores = servicios.importar_lista(seccion, texto_de(61))

    assert cantidad == 0
    assert titulos(errores) == ["La lista tiene 61 líneas; el máximo es 60"]
    assert seccion.estudiantes.count() == 0


def test_pegar_lista_con_la_seccion_con_un_estudiante_no_guarda_nada(seccion):
    crear(seccion, "QUISPE MAMANI, ANA")

    with pytest.raises(servicios.SeccionConEstudiantes):
        servicios.importar_lista(seccion, texto_de(25))

    assert seccion.estudiantes.count() == 1


def test_con_estudiantes_ni_siquiera_lee_el_texto(seccion):
    crear(seccion, "QUISPE MAMANI, ANA")

    with pytest.raises(servicios.SeccionConEstudiantes):
        servicios.importar_lista(seccion, "texto sin coma")


def test_importar_con_un_nombre_igual_en_otra_seccion_se_guarda(seccion):
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")
    crear(otra, "QUISPE MAMANI, ANA")

    cantidad, _ = servicios.importar_lista(seccion, "QUISPE MAMANI, ANA")

    assert cantidad == 1


# --- estudiantes_ordenados ---


def nombres_ordenados(seccion):
    return [str(e) for e in servicios.estudiantes_ordenados(seccion)]


def test_alvarez_va_antes_de_bravo(seccion):
    crear(seccion, "BRAVO, LUIS", "ÁLVAREZ, ROSA")

    assert nombres_ordenados(seccion) == ["ÁLVAREZ, ROSA", "BRAVO, LUIS"]


def test_nunez_va_antes_de_nuñez(seccion):
    crear(seccion, "NUÑEZ, ANA", "NUNEZ, ANA")

    assert nombres_ordenados(seccion) == ["NUNEZ, ANA", "NUÑEZ, ANA"]


def test_ñaupa_va_antes_de_ochoa(seccion):
    crear(seccion, "OCHOA, LUIS", "ÑAUPA, ROSA", "NAVARRO, PEDRO")

    assert nombres_ordenados(seccion) == ["NAVARRO, PEDRO", "ÑAUPA, ROSA", "OCHOA, LUIS"]


def test_el_orden_desempata_por_nombres(seccion):
    crear(seccion, "QUISPE, LUCÍA", "QUISPE, ANA")

    assert nombres_ordenados(seccion) == ["QUISPE, ANA", "QUISPE, LUCÍA"]


def test_lista_vacia_se_ordena_sin_error(seccion):
    assert servicios.estudiantes_ordenados(seccion) == []


# --- agregar_estudiante y editar_estudiante ---


def test_agregar_normaliza_y_guarda(seccion):
    estudiante = servicios.agregar_estudiante(seccion, "  quispe   mamani ", "ana lucía")

    estudiante.refresh_from_db()
    assert str(estudiante) == "QUISPE MAMANI, ANA LUCÍA"
    assert estudiante.seccion == seccion


def test_agregar_el_homonimo_se_rechaza_y_no_cambia_nada(seccion):
    crear(seccion, "QUISPE MAMANI, ANA")

    with pytest.raises(ValidationError) as error:
        servicios.agregar_estudiante(seccion, "quispe mamani", "ana")

    assert HOMONIMO in error.value.messages
    assert seccion.estudiantes.count() == 1


@pytest.mark.parametrize(
    ("apellidos", "nombres"), [("", "ANA"), ("QUISPE", "  "), ("A" * 121, "B")]
)
def test_agregar_rechaza_campos_vacios_o_largos(seccion, apellidos, nombres):
    with pytest.raises(ValidationError):
        servicios.agregar_estudiante(seccion, apellidos, nombres)

    assert seccion.estudiantes.count() == 0


def test_editar_normaliza_y_guarda(seccion):
    crear(seccion, "QUISPE MAMANI, ANA LUCIA")
    estudiante = seccion.estudiantes.get()

    servicios.editar_estudiante(estudiante, "quispe mamani", "ana lucía")

    estudiante.refresh_from_db()
    assert str(estudiante) == "QUISPE MAMANI, ANA LUCÍA"


def test_editar_sin_cambios_no_choca_consigo_mismo(seccion):
    crear(seccion, "QUISPE MAMANI, ANA")
    estudiante = seccion.estudiantes.get()

    servicios.editar_estudiante(estudiante, "quispe mamani", "ana")

    assert seccion.estudiantes.count() == 1


def test_editar_hacia_un_homonimo_se_rechaza_y_no_cambia_nada(seccion):
    crear(seccion, "QUISPE MAMANI, ANA", "QUISPE MAMANI, ANA LUCIA")
    estudiante = seccion.estudiantes.get(nombres="ANA LUCIA")

    with pytest.raises(ValidationError) as error:
        servicios.editar_estudiante(estudiante, "Quispe Mamani", "Ana")

    assert HOMONIMO in error.value.messages
    estudiante.refresh_from_db()
    assert estudiante.nombres == "ANA LUCIA"


# --- quitar_estudiante y vaciar_lista ---


@pytest.fixture
def borrado_con_registros(monkeypatch):
    """Simula un registro que apunta al estudiante: borra y luego lanza ``RestrictedError``.

    Así la prueba comprueba que el servicio deshace lo borrado (hasta que US-030 cree
    ``asistencia`` con ``RESTRICT``, design de US-006, D2).
    """
    original_queryset = QuerySet.delete
    original_modelo = Estudiante.delete

    def queryset_delete(self):
        if self.model is Estudiante:
            original_queryset(self)
            raise RestrictedError("simulado", set())
        return original_queryset(self)

    def modelo_delete(self, *args, **kwargs):
        original_modelo(self, *args, **kwargs)
        raise RestrictedError("simulado", set())

    monkeypatch.setattr(QuerySet, "delete", queryset_delete)
    monkeypatch.setattr(Estudiante, "delete", modelo_delete)


def test_quitar_sin_registros_lo_borra(seccion):
    crear(seccion, "QUISPE, ANA", "RAMOS, LUIS")

    servicios.quitar_estudiante(seccion.estudiantes.get(apellidos="QUISPE"))

    assert nombres_ordenados(seccion) == ["RAMOS, LUIS"]


def test_vaciar_sin_registros_borra_a_todos(seccion):
    crear(seccion, "QUISPE, ANA", "RAMOS, LUIS")

    servicios.vaciar_lista(seccion)

    assert seccion.estudiantes.count() == 0


def test_vaciar_no_toca_otras_secciones(seccion):
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")
    crear(seccion, "QUISPE, ANA")
    crear(otra, "QUISPE, ANA")

    servicios.vaciar_lista(seccion)

    assert otra.estudiantes.count() == 1


def test_quitar_con_registros_lanza_y_no_borra(seccion, borrado_con_registros):
    crear(seccion, "QUISPE, ANA")

    with pytest.raises(servicios.ListaConRegistros):
        servicios.quitar_estudiante(seccion.estudiantes.get())

    assert seccion.estudiantes.count() == 1


def test_vaciar_con_registros_lanza_y_no_borra_ninguno(seccion, borrado_con_registros):
    crear(seccion, "QUISPE, ANA", "RAMOS, LUIS", "SOTO, PEDRO")

    with pytest.raises(servicios.ListaConRegistros):
        servicios.vaciar_lista(seccion)

    assert seccion.estudiantes.count() == 3


# --- secciones de la docente ---


def test_secciones_docente_ordena_y_excluye_el_anio_cerrado(seccion, docente):
    seccion.docente = docente
    seccion.save()
    b = Seccion.objects.create(
        anio_escolar=seccion.anio_escolar, grado=1, nombre="B", docente=docente
    )
    cerrado = AnioEscolar.objects.create(
        institucion=seccion.anio_escolar.institucion, anio=2026, estado="CERRADO"
    )
    Seccion.objects.create(anio_escolar=cerrado, grado=1, nombre="A", docente=docente)

    assert list(servicios.secciones_docente(docente)) == [b, seccion]


def test_seccion_unica_con_su_cantidad(seccion, docente):
    seccion.docente = docente
    seccion.save()
    crear(seccion, "QUISPE, ANA", "RAMOS, LUIS")

    unica = servicios.seccion_unica(docente)

    assert unica == seccion
    assert unica.cantidad_estudiantes == 2


def test_seccion_unica_sin_estudiantes_tiene_cantidad_cero(seccion, docente):
    seccion.docente = docente
    seccion.save()

    assert servicios.seccion_unica(docente).cantidad_estudiantes == 0


def test_seccion_unica_es_none_con_dos_secciones(seccion, docente):
    seccion.docente = docente
    seccion.save()
    Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B", docente=docente)

    assert servicios.seccion_unica(docente) is None


def test_seccion_unica_es_none_sin_secciones(docente):
    assert servicios.seccion_unica(docente) is None


def test_texto_seccion_corto(seccion):
    assert servicios.texto_seccion_corto(seccion) == "2.º A"
