"""Carga, edición y eliminación de una sesión de referencia (spec material-referencia; design de
US-018, D4).

El Administrador las carga desde el panel; aquí se prueba el servicio que llama la ficha. Todo o
nada, como el envío de una docente: la fila, su entrada y el archivo se guardan juntos o no se
guarda ninguno.
"""

import pytest
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied, ValidationError
from django.core.files.storage import storages
from django.db import transaction

from actividad.models import Operacion, RegistroActividad
from catalogo.models import InstitucionArea
from repositorio import servicios
from repositorio.models import TIPO_DOCX, TIPO_PDF, Sesion, SesionVista
from repositorio.tests.archivos import docx_con_texto, pdf, pdf_con_texto, subido

pytestmark = pytest.mark.django_db

FUENTE_Y_PERMISO = "Indique la fuente y el permiso de uso"
PERMISO = "Uso libre con fines educativos, citando la fuente."


@pytest.fixture
def almacen():
    return storages["sesiones"]


@pytest.fixture
def datos(institucion, comunicacion):
    """Lo que manda la ficha: «Leemos un cuento», 3.º a 5.º grado, Comunicación."""

    def armar(**cambios):
        valores = {
            "institucion": str(institucion.pk),
            "grado": "3",
            "grado_hasta": "5",
            "area": str(comunicacion.pk),
            "titulo": "Leemos un cuento",
            "proposito": "Que lean un cuento y cuenten lo que entendieron.",
            "fuente": "Minedu, Aprendo en casa 2021",
            "permiso_uso": PERMISO,
            **cambios,
        }
        return {clave: valor for clave, valor in valores.items() if valor is not None}

    return armar


@pytest.fixture
def cargar(administrador, datos):
    """Carga una sesión de referencia con los datos de ``datos`` y un PDF."""

    def cargar_una(archivo=None, **cambios):
        return servicios.cargar_referencia(administrador, datos(**cambios), archivo or pdf())

    return cargar_una


def errores_al_cargar(administrador, datos, archivo):
    with pytest.raises(ValidationError) as error:
        servicios.cargar_referencia(administrador, datos, archivo)
    return {campo: mensajes[0] for campo, mensajes in error.value.message_dict.items()}


def nada_guardado(almacen):
    assert not Sesion.objects.exists()
    assert not RegistroActividad.objects.filter(
        operacion=Operacion.SESION_REFERENCIA_CARGADA
    ).exists()
    assert not almacen.exists("sesiones") or almacen.listdir("sesiones") == ([], [])


def entradas(operacion):
    return list(RegistroActividad.objects.filter(operacion=operacion).order_by("id"))


# --- Cargar una sesión de referencia ---------------------------------------------------------


def test_camino_ideal_la_guarda_como_material_de_referencia_sin_autora(
    administrador, institucion, comunicacion, cargar, almacen
):
    sesion = cargar(pdf("Leemos un cuento.pdf"))

    sesion = Sesion.objects.get(pk=sesion.pk)
    assert sesion.origen == Sesion.Origen.REFERENCIA
    assert sesion.autor is None
    assert sesion.subido_por == administrador
    assert sesion.institucion == institucion
    assert (sesion.grado, sesion.grado_hasta) == (3, 5)
    assert sesion.area == comunicacion
    assert sesion.titulo == "Leemos un cuento"
    assert sesion.fuente == "Minedu, Aprendo en casa 2021"
    assert sesion.permiso_uso == PERMISO
    assert sesion.estado == ""
    assert sesion.compartida is True
    assert sesion.terminos_aceptados_en is None
    assert sesion.archivo_nombre == "Leemos un cuento.pdf"
    assert sesion.tipo_mime == TIPO_PDF
    with almacen.open(sesion.archivo_clave) as guardado:
        assert guardado.read() == pdf().open().read()


def test_fuente_equipo_del_proyecto_se_guarda(cargar):
    # Escenario «Flujo alternativo válido (equipo del proyecto)».
    sesion = cargar(fuente="Equipo del proyecto")

    assert Sesion.objects.get(pk=sesion.pk).fuente == "Equipo del proyecto"


def test_los_textos_se_recortan_y_el_proposito_es_opcional(cargar):
    sesion = cargar(titulo="  Leemos  ", proposito="", fuente="  Equipo del proyecto ")

    sesion.refresh_from_db()
    assert (sesion.titulo, sesion.proposito, sesion.fuente) == ("Leemos", "", "Equipo del proyecto")


def test_un_solo_grado_es_un_rango_de_uno(cargar):
    sesion = cargar(grado="4", grado_hasta="4")

    assert (sesion.grado, sesion.grado_hasta) == (4, 4)


def test_visible_desde_que_se_guarda_solo_en_su_institucion(cargar, docente, colega_de_otra):
    sesion = cargar()

    assert servicios.sesion_visible(docente, sesion.pk) is not None
    assert [s.pk for s in servicios.buscar_repositorio(docente).sesiones] == [sesion.pk]
    assert servicios.sesion_visible(colega_de_otra, sesion.pk) is None
    assert servicios.buscar_repositorio(colega_de_otra).sesiones == []


def test_solo_el_administrador_carga(docente, datos, almacen):
    with pytest.raises(PermissionDenied):
        servicios.cargar_referencia(docente, datos(), pdf())

    nada_guardado(almacen)


# --- Fuente y permiso de uso obligatorios -----------------------------------------------------


@pytest.mark.parametrize(
    "cambios",
    [
        {"fuente": ""},
        {"permiso_uso": ""},
        {"fuente": None},
        {"permiso_uso": None},
        {"fuente": "   "},
        {"permiso_uso": " \t "},
        {"fuente": "", "permiso_uso": ""},
    ],
    ids=[
        "sin-fuente",
        "sin-permiso",
        "fuente-ausente",
        "permiso-ausente",
        "fuente-espacios",
        "permiso-espacios",
        "sin-ambos",
    ],
)
def test_sin_fuente_o_permiso_no_guarda_nada_y_lo_dice(administrador, datos, almacen, cambios):
    # Escenarios «Caso de error» y «Solo espacios».
    errores = errores_al_cargar(administrador, datos(**cambios), pdf())

    assert errores == {NON_FIELD_ERRORS: FUENTE_Y_PERMISO}
    nada_guardado(almacen)


@pytest.mark.parametrize("campo", ["fuente", "permiso_uso"])
def test_fuente_y_permiso_de_300_se_guardan(cargar, campo):
    assert getattr(cargar(**{campo: "a" * 300}), campo) == "a" * 300


@pytest.mark.parametrize(
    ("campo", "mensaje"),
    [
        ("fuente", "La fuente puede tener hasta 300 caracteres."),
        ("permiso_uso", "El permiso de uso puede tener hasta 300 caracteres."),
    ],
)
def test_fuente_y_permiso_de_301_no_se_guardan(administrador, datos, almacen, campo, mensaje):
    errores = errores_al_cargar(administrador, datos(**{campo: "a" * 301}), pdf())

    assert errores == {campo: mensaje}
    nada_guardado(almacen)


# --- Varios grados ----------------------------------------------------------------------------


def test_rango_al_reves_no_se_guarda(administrador, datos, almacen):
    errores = errores_al_cargar(administrador, datos(grado="5", grado_hasta="3"), pdf())

    assert errores == {"grado_hasta": "El grado final no puede ser menor que el inicial."}
    nada_guardado(almacen)


@pytest.mark.parametrize(
    ("cambios", "errores"),
    [
        ({"grado": ""}, {"grado": "Falta indicar el grado."}),
        ({"grado_hasta": ""}, {"grado_hasta": "Falta indicar el grado final."}),
        ({"grado": "0"}, {"grado": "Elige un grado de la lista."}),
        ({"grado_hasta": "7"}, {"grado_hasta": "Elige un grado de la lista."}),
    ],
    ids=["sin-grado", "sin-grado-final", "grado-0", "grado-final-7"],
)
def test_grados_fuera_de_la_lista(administrador, datos, almacen, cambios, errores):
    assert errores_al_cargar(administrador, datos(**cambios), pdf()) == errores
    nada_guardado(almacen)


# --- Datos y archivo válidos ------------------------------------------------------------------


def test_area_que_la_institucion_elegida_no_trabaja(
    administrador, institucion, otra_institucion, comunicacion, datos, almacen
):
    # La otra institución sí la trabaja: cuenta la elegida, no otra.
    InstitucionArea.objects.filter(institucion=institucion, area=comunicacion).update(
        se_trabaja=False
    )
    assert InstitucionArea.objects.get(institucion=otra_institucion, area=comunicacion).se_trabaja

    errores = errores_al_cargar(administrador, datos(), pdf())

    assert errores == {"area": "Elige un área de la lista."}
    nada_guardado(almacen)


def test_la_institucion_elegida_es_obligatoria_y_debe_existir(administrador, datos, almacen):
    assert errores_al_cargar(administrador, datos(institucion=""), pdf()) == {
        "institucion": "Falta indicar la institución."
    }
    assert errores_al_cargar(administrador, datos(institucion="999999"), pdf()) == {
        "institucion": "Elige una institución de la lista."
    }
    nada_guardado(almacen)


def test_la_carga_en_otra_institucion_queda_en_la_suya(
    administrador, otra_institucion, datos, docente, colega_de_otra
):
    sesion = servicios.cargar_referencia(
        administrador, datos(institucion=str(otra_institucion.pk)), pdf()
    )

    assert sesion.institucion == otra_institucion
    assert servicios.sesion_visible(colega_de_otra, sesion.pk) is not None
    assert servicios.sesion_visible(docente, sesion.pk) is None


def test_sin_titulo_y_con_proposito_largo_dice_cada_motivo(administrador, datos, almacen):
    errores = errores_al_cargar(administrador, datos(titulo=" ", proposito="b" * 1001), pdf())

    assert errores == {
        "titulo": "Falta indicar el título.",
        "proposito": "El propósito puede tener hasta 1000 caracteres.",
    }
    nada_guardado(almacen)


def test_archivo_que_no_es_pdf_ni_word(administrador, datos, almacen):
    errores = errores_al_cargar(administrador, datos(), subido("foto.pdf", b"\x89PNG\r\n\x1a\n"))

    assert errores == {"archivo": "Este archivo no es PDF ni Word (.docx). Elige otro archivo."}
    nada_guardado(almacen)


def test_sin_archivo(administrador, datos, almacen):
    errores = errores_al_cargar(administrador, datos(), None)

    assert errores == {"archivo": "Elige un archivo PDF o Word (.docx)."}
    nada_guardado(almacen)


# --- Texto para la búsqueda -------------------------------------------------------------------


def test_una_palabra_del_docx_la_encuentra_en_el_repositorio(cargar, docente, almacen):
    contenido = docx_con_texto(["Formamos equipos multigrado"])

    sesion = cargar(subido("sesion.docx", contenido))

    sesion.refresh_from_db()
    assert sesion.tipo_mime == TIPO_DOCX
    assert sesion.texto == "Formamos equipos multigrado"
    pagina = servicios.buscar_repositorio(docente, q="multigrado")
    assert [s.pk for s in pagina.sesiones] == [sesion.pk]
    with almacen.open(sesion.archivo_clave) as guardado:
        assert guardado.read() == contenido


def test_un_pdf_escaneado_se_guarda_sin_texto_y_sin_error(cargar):
    sesion = cargar(subido("escaneada.pdf", pdf_con_texto([[], []])))

    sesion.refresh_from_db()
    assert sesion.texto == ""
    assert sesion.texto_busqueda.startswith("leemos un cuento")


# --- Registro de la carga ---------------------------------------------------------------------


def test_cargar_deja_sesion_referencia_cargada_y_ninguna_sesion_enviada(administrador, cargar):
    sesion = cargar()

    (entrada,) = entradas(Operacion.SESION_REFERENCIA_CARGADA)
    assert entrada.usuario == administrador
    assert (entrada.entidad, entrada.entidad_id) == ("sesion", str(sesion.pk))
    assert entrada.detalle == {}
    assert entradas(Operacion.SESION_ENVIADA) == []


def test_falla_el_almacenamiento_no_deja_fila_ni_entrada(
    administrador, datos, almacen, monkeypatch
):
    def rechazar(*args, **kwargs):
        raise OSError("R2 no responde")

    monkeypatch.setattr(almacen, "save", rechazar)

    with pytest.raises(OSError):
        servicios.cargar_referencia(administrador, datos(), pdf())

    nada_guardado(almacen)


# --- Editar -----------------------------------------------------------------------------------


def datos_de(sesion, **cambios):
    valores = {
        "institucion": str(sesion.institucion_id),
        "grado": str(sesion.grado),
        "grado_hasta": str(sesion.grado_hasta),
        "area": str(sesion.area_id),
        "titulo": sesion.titulo,
        "proposito": sesion.proposito,
        "fuente": sesion.fuente,
        "permiso_uso": sesion.permiso_uso,
        **cambios,
    }
    return valores


def test_editar_titulo_y_fuente_deja_sesion_referencia_editada_con_los_campos(
    administrador, cargar, docente
):
    sesion = cargar(subido("sesion.docx", docx_con_texto(["Formamos equipos"])))

    servicios.editar_referencia(
        administrador,
        sesion,
        datos_de(sesion, titulo="Cuidamos el árbol", fuente="Equipo del proyecto"),
    )

    sesion.refresh_from_db()
    assert sesion.titulo == "Cuidamos el árbol"
    assert sesion.fuente == "Equipo del proyecto"
    (entrada,) = entradas(Operacion.SESION_REFERENCIA_EDITADA)
    assert entrada.usuario == administrador
    assert (entrada.entidad, entrada.entidad_id) == ("sesion", str(sesion.pk))
    assert sorted(entrada.detalle["campos"]) == ["fuente", "titulo"]
    assert "Cuidamos" not in str(entrada.detalle)
    # El texto de búsqueda se recalcula con el texto guardado.
    assert (
        sesion.texto_busqueda == "cuidamos el arbol que lean un cuento y cuenten lo que "
        "entendieron. formamos equipos"
    )
    assert [s.pk for s in servicios.buscar_repositorio(docente, q="árbol").sesiones] == [sesion.pk]
    assert servicios.buscar_repositorio(docente, q="leemos").sesiones == []


def test_editar_los_grados_y_el_area(administrador, cargar, matematica):
    sesion = cargar()

    servicios.editar_referencia(
        administrador, sesion, datos_de(sesion, grado="1", grado_hasta="2", area=str(matematica.pk))
    )

    sesion.refresh_from_db()
    assert (sesion.grado, sesion.grado_hasta, sesion.area) == (1, 2, matematica)
    (entrada,) = entradas(Operacion.SESION_REFERENCIA_EDITADA)
    assert sorted(entrada.detalle["campos"]) == ["area", "grado", "grado_hasta"]


def test_guardar_sin_cambios_no_deja_entrada(administrador, cargar):
    sesion = cargar()

    servicios.editar_referencia(administrador, sesion, datos_de(sesion))

    assert entradas(Operacion.SESION_REFERENCIA_EDITADA) == []


def test_editar_no_cambia_la_institucion_ni_el_archivo(
    administrador, cargar, otra_institucion, almacen
):
    sesion = cargar()
    clave = sesion.archivo_clave

    servicios.editar_referencia(
        administrador, sesion, datos_de(sesion, institucion=str(otra_institucion.pk))
    )

    sesion.refresh_from_db()
    assert sesion.institucion_id != otra_institucion.pk
    assert sesion.archivo_clave == clave
    assert almacen.exists(clave)
    assert entradas(Operacion.SESION_REFERENCIA_EDITADA) == []


def test_borrar_la_fuente_al_editar_no_guarda_el_cambio(administrador, cargar):
    sesion = cargar()

    with pytest.raises(ValidationError) as error:
        servicios.editar_referencia(
            administrador, sesion, datos_de(sesion, fuente=" ", titulo="Otro título")
        )

    assert error.value.message_dict == {NON_FIELD_ERRORS: [FUENTE_Y_PERMISO]}
    sesion.refresh_from_db()
    assert (sesion.fuente, sesion.titulo) == ("Minedu, Aprendo en casa 2021", "Leemos un cuento")
    assert entradas(Operacion.SESION_REFERENCIA_EDITADA) == []


def test_editar_una_sesion_de_docente_no_se_puede(administrador, docente, crear_sesion):
    sesion = crear_sesion(docente)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.editar_referencia(administrador, sesion, datos_de(sesion, titulo="Otro"))

    sesion.refresh_from_db()
    assert sesion.titulo == "Leemos un cuento"


def test_solo_el_administrador_edita(docente, cargar):
    sesion = cargar()

    with pytest.raises(PermissionDenied):
        servicios.editar_referencia(docente, sesion, datos_de(sesion, titulo="Otro"))


# --- Eliminar ---------------------------------------------------------------------------------


def test_eliminar_borra_fila_vistas_y_al_confirmar_el_archivo(
    administrador, cargar, docente, almacen, django_capture_on_commit_callbacks
):
    sesion = cargar()
    servicios.registrar_vista(docente, sesion)
    assert SesionVista.objects.filter(sesion=sesion).exists()

    with django_capture_on_commit_callbacks(execute=False) as al_confirmar:
        with transaction.atomic():
            servicios.eliminar_referencia(administrador, sesion)
    assert almacen.exists(sesion.archivo_clave)
    for llamada in al_confirmar:
        llamada()

    assert not Sesion.objects.filter(pk=sesion.pk).exists()
    assert not SesionVista.objects.exists()
    assert not almacen.exists(sesion.archivo_clave)
    assert servicios.sesion_visible(docente, sesion.pk) is None
    (entrada,) = entradas(Operacion.SESION_REFERENCIA_ELIMINADA)
    assert entrada.usuario == administrador
    assert (entrada.entidad, entrada.entidad_id) == ("sesion", str(sesion.pk))
    assert entrada.detalle == {}


def test_eliminar_una_sesion_de_docente_no_se_puede(administrador, docente, con_archivo, almacen):
    sesion = con_archivo(docente)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.eliminar_referencia(administrador, sesion)

    assert Sesion.objects.filter(pk=sesion.pk).exists()
    assert almacen.exists(sesion.archivo_clave)
    assert entradas(Operacion.SESION_REFERENCIA_ELIMINADA) == []


def test_solo_el_administrador_elimina(docente, cargar):
    sesion = cargar()

    with pytest.raises(PermissionDenied):
        servicios.eliminar_referencia(docente, sesion)

    assert Sesion.objects.filter(pk=sesion.pk).exists()
