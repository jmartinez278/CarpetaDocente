"""Envío de una sesión (specs envio-sesiones, almacenamiento-archivos y registro-actividad;
design D4, D5, D6 y D10).

Todo o nada: la sesión, su entrada SESION_ENVIADA y su archivo se guardan juntos o no se guarda
ninguno. Un envío repetido con el mismo ``id`` responde el mismo éxito sin escribir otra vez.
"""

import re
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import DatabaseError, connection
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from catalogo.models import Area, InstitucionArea
from institucion.models import AnioEscolar, Seccion
from repositorio import servicios
from repositorio.models import TAMANO_MAXIMO, TIPO_DOCX, TIPO_PDF, Sesion
from repositorio.tests.archivos import docx, pdf, subido
from repositorio.tests.conftest import COMUNICACION, MATEMATICA

pytestmark = pytest.mark.django_db

GENERAL = "No se pudo enviar. Recarga la página e intenta de nuevo."
TERMINOS = "Para compartirla en el repositorio debes aceptar los términos."


@pytest.fixture
def almacen():
    return storages["sesiones"]


@pytest.fixture
def datos(comunicacion):
    """Lo que manda el formulario: «Leemos un cuento», 2.º grado, Comunicación, sin compartir."""

    def armar(**cambios):
        valores = {
            "id": str(uuid.uuid4()),
            "grado": "2",
            "area": str(comunicacion.pk),
            "titulo": "Leemos un cuento",
            "proposito": "Que lean un cuento y cuenten lo que entendieron.",
            **cambios,
        }
        return {clave: valor for clave, valor in valores.items() if valor is not None}

    return armar


def errores_de(usuario, datos, archivo):
    with pytest.raises(ValidationError) as error:
        servicios.enviar_sesion(usuario, datos, archivo)
    return {campo: mensajes[0] for campo, mensajes in error.value.message_dict.items()}


def clave_de(id_, extension):
    """La clave de un intento: ``sesiones/<UUID>-<16 hex><extensión>`` (D4)."""
    return re.compile(rf"sesiones/{re.escape(id_)}-[0-9a-f]{{16}}{re.escape(extension)}")


def nada_guardado(almacen):
    assert not Sesion.objects.exists()
    assert not RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).exists()
    assert not almacen.exists("sesiones") or almacen.listdir("sesiones") == ([], [])


# --- Sesión guardada -------------------------------------------------------------------------


def test_enviar_sin_compartir_guarda_la_sesion_con_sus_datos(
    docente, institucion, comunicacion, datos, almacen
):
    # Escenarios «Datos guardados» y «Enviar sin compartir».
    enviados = datos()

    sesion = servicios.enviar_sesion(docente, enviados, pdf("Leemos un cuento.pdf"))

    sesion = Sesion.objects.get(pk=sesion.pk)
    assert str(sesion.pk) == enviados["id"]
    assert sesion.institucion == institucion
    assert sesion.autor == docente
    assert sesion.subido_por == docente
    assert sesion.grado == 2
    assert sesion.area == comunicacion
    assert sesion.titulo == "Leemos un cuento"
    assert sesion.proposito == "Que lean un cuento y cuenten lo que entendieron."
    assert sesion.origen == Sesion.Origen.PROPIA
    assert sesion.estado == Sesion.Estado.ENVIADA
    assert sesion.compartida is False
    assert sesion.terminos_aceptados_en is None
    assert sesion.archivo_nombre == "Leemos un cuento.pdf"
    assert sesion.tipo_mime == TIPO_PDF
    assert sesion.tamano_bytes == pdf().size


def test_clave_de_un_pdf_es_sesiones_uuid_token_pdf_y_el_archivo_esta_en_el_almacen(
    docente, datos, almacen
):
    # Escenario «Clave de un PDF».
    enviados = datos()
    archivo = pdf("Leemos un cuento.pdf")

    sesion = servicios.enviar_sesion(docente, enviados, archivo)

    assert clave_de(enviados["id"], ".pdf").fullmatch(sesion.archivo_clave)
    with almacen.open(sesion.archivo_clave) as guardado:
        assert guardado.read() == archivo.open().read()


def test_un_docx_se_guarda_con_su_tipo_y_su_clave(docente, datos):
    enviados = datos()

    sesion = servicios.enviar_sesion(docente, enviados, docx())

    assert sesion.tipo_mime == TIPO_DOCX
    assert clave_de(enviados["id"], ".docx").fullmatch(sesion.archivo_clave)


def test_justo_4_mb_se_guarda(docente, datos):
    # Escenario «Justo 4 MB».
    sesion = servicios.enviar_sesion(docente, datos(), pdf(tamano=TAMANO_MAXIMO))

    assert sesion.tamano_bytes == TAMANO_MAXIMO


def test_el_proposito_es_opcional_y_los_textos_se_recortan(docente, datos):
    sesion = servicios.enviar_sesion(
        docente, datos(titulo="  Leemos un cuento  ", proposito=None), pdf()
    )

    assert sesion.titulo == "Leemos un cuento"
    assert sesion.proposito == ""


def test_docente_sin_seccion_tambien_envia(docente, datos):
    # Escenario «Docente sin sección»: Sesiones no depende de tener sección.
    assert not Seccion.objects.filter(docente=docente).exists()

    servicios.enviar_sesion(docente, datos(), pdf())

    assert Sesion.objects.filter(autor=docente).count() == 1


# --- Compartir y términos --------------------------------------------------------------------


def test_aceptar_y_enviar_la_deja_compartida_con_la_fecha_de_aceptacion(docente, datos):
    # Escenario «Aceptar y enviar».
    antes = timezone.now()

    sesion = servicios.enviar_sesion(docente, datos(compartir="on", acepta_terminos="1"), pdf())

    sesion.refresh_from_db()
    assert sesion.compartida is True
    assert antes <= sesion.terminos_aceptados_en <= timezone.now()


def test_compartir_sin_aceptar_no_guarda_nada(docente, datos, almacen):
    # Escenario «Compartir sin aceptar».
    errores = errores_de(docente, datos(compartir="on"), pdf())

    assert errores == {"compartir": TERMINOS}
    nada_guardado(almacen)


def test_aceptar_sin_compartir_no_la_comparte(docente, datos):
    sesion = servicios.enviar_sesion(docente, datos(acepta_terminos="1"), pdf())

    assert sesion.compartida is False
    assert sesion.terminos_aceptados_en is None


# --- Datos que faltan ------------------------------------------------------------------------


def test_sin_grado_area_titulo_ni_archivo_dice_cada_motivo(docente, datos, almacen):
    # Escenarios «Área y título vacíos» y «Sin archivo».
    errores = errores_de(docente, datos(grado="", area="", titulo="   "), None)

    assert errores == {
        "grado": "Falta indicar el grado.",
        "area": "Falta indicar el área.",
        "titulo": "Falta indicar el título.",
        "archivo": "Elige un archivo PDF o Word (.docx).",
    }
    nada_guardado(almacen)


def test_campos_ausentes_son_datos_que_faltan(docente, almacen):
    errores = errores_de(docente, {"id": str(uuid.uuid4())}, pdf())

    assert set(errores) == {"grado", "area", "titulo"}
    nada_guardado(almacen)


@pytest.mark.parametrize(
    ("cambios", "campo", "mensaje"),
    [
        ({"grado": "7"}, "grado", "Elige un grado de la lista."),
        ({"grado": "0"}, "grado", "Elige un grado de la lista."),
        ({"grado": "dos"}, "grado", "Elige un grado de la lista."),
        ({"area": "999999"}, "area", "Elige un área de la lista."),
        ({"area": "abc"}, "area", "Elige un área de la lista."),
        ({"titulo": "a" * 201}, "titulo", "El título puede tener hasta 200 caracteres."),
        ({"proposito": "a" * 1001}, "proposito", "El propósito puede tener hasta 1000 caracteres."),
    ],
    ids=[
        "grado-7",
        "grado-0",
        "grado-texto",
        "area-inexistente",
        "area-texto",
        "titulo-201",
        "proposito-1001",
    ],
)
def test_dato_fuera_de_rango_dice_su_motivo(docente, datos, almacen, cambios, campo, mensaje):
    # Escenario «Área ajena o grado fuera de rango».
    assert errores_de(docente, datos(**cambios), pdf()) == {campo: mensaje}
    nada_guardado(almacen)


def test_titulo_de_200_y_proposito_de_1000_se_guardan(docente, datos):
    sesion = servicios.enviar_sesion(docente, datos(titulo="a" * 200, proposito="b" * 1000), pdf())

    assert (len(sesion.titulo), len(sesion.proposito)) == (200, 1000)


def test_area_que_la_institucion_no_trabaja_se_rechaza(docente, institucion, datos, almacen):
    matematica = Area.objects.get(codigo_siagie=MATEMATICA)
    InstitucionArea.objects.filter(institucion=institucion, area=matematica).update(
        se_trabaja=False
    )

    errores = errores_de(docente, datos(area=str(matematica.pk)), pdf())

    assert errores == {"area": "Elige un área de la lista."}
    nada_guardado(almacen)


def test_area_de_otra_institucion_que_la_mia_no_trabaja_se_rechaza(
    docente, institucion, otra_institucion, comunicacion, datos, almacen
):
    InstitucionArea.objects.filter(institucion=institucion, area=comunicacion).update(
        se_trabaja=False
    )
    assert InstitucionArea.objects.get(institucion=otra_institucion, area=comunicacion).se_trabaja

    assert errores_de(docente, datos(), pdf()) == {"area": "Elige un área de la lista."}
    nada_guardado(almacen)


@pytest.mark.parametrize(
    ("archivo", "mensaje"),
    [
        (
            subido("sesion.pdf", b"MZ\x90\x00"),
            "Este archivo no es PDF ni Word (.docx). Elige otro archivo.",
        ),
        (
            subido("sesion.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
            "Este archivo no es PDF ni Word (.docx). Elige otro archivo.",
        ),
        (subido("sesion.pdf", b""), "Este archivo no es PDF ni Word (.docx). Elige otro archivo."),
        (pdf(tamano=TAMANO_MAXIMO + 1), "El archivo supera los 4 MB. Elige uno más pequeño."),
    ],
    ids=["otro-tipo", "doc", "vacio", "4194305"],
)
def test_archivo_que_salta_el_navegador_no_se_guarda(docente, datos, almacen, archivo, mensaje):
    # Escenario «Envío que salta el navegador».
    assert errores_de(docente, datos(), archivo) == {"archivo": mensaje}
    nada_guardado(almacen)


# --- Sin archivos huérfanos ------------------------------------------------------------------


def test_falla_el_almacenamiento_no_deja_sesion_ni_entrada(docente, datos, almacen, monkeypatch):
    # Escenario «Falla el almacenamiento»: la vista responde el error de conexión.
    def rechazar(*args, **kwargs):
        raise OSError("R2 no responde")

    monkeypatch.setattr(almacen, "save", rechazar)

    with pytest.raises(OSError):
        servicios.enviar_sesion(docente, datos(), pdf())

    nada_guardado(almacen)


def test_almacen_que_guarda_con_otro_nombre_no_deja_nada(docente, datos, almacen, monkeypatch):
    guardar = almacen.save

    def renombrar(nombre, contenido, **kwargs):
        return guardar(nombre.replace(".pdf", "_abc.pdf"), contenido, **kwargs)

    monkeypatch.setattr(almacen, "save", renombrar)

    with pytest.raises(RuntimeError):
        servicios.enviar_sesion(docente, datos(), pdf())

    nada_guardado(almacen)


def test_falla_la_base_despues_del_archivo_borra_el_archivo(docente, datos, almacen, monkeypatch):
    # Escenario «Falla la base después del archivo»: falla la confirmación de la transacción.
    confirmar = connection.savepoint_commit
    fallas = []

    def fallar_una_vez(sid):
        if not fallas:
            fallas.append(sid)
            raise DatabaseError("se cayó la base al confirmar")
        return confirmar(sid)

    monkeypatch.setattr(connection, "savepoint_commit", fallar_una_vez)

    with pytest.raises(DatabaseError):
        servicios.enviar_sesion(docente, datos(), pdf())

    monkeypatch.undo()
    assert fallas
    nada_guardado(almacen)


def test_el_almacen_escribe_y_luego_falla_no_deja_el_archivo(docente, datos, almacen, monkeypatch):
    # A2, hallazgo 2: ``save`` llegó a escribir y lanzó antes de devolver la clave.
    guardar = almacen.save

    def escribir_y_fallar(nombre, contenido, **kwargs):
        guardar(nombre, contenido, **kwargs)
        raise OSError("se cortó la respuesta de R2")

    monkeypatch.setattr(almacen, "save", escribir_y_fallar)

    with pytest.raises(OSError):
        servicios.enviar_sesion(docente, datos(), pdf())

    nada_guardado(almacen)


def test_el_intento_que_falla_no_borra_el_archivo_del_reintento_que_gano(
    docente, datos, almacen, monkeypatch
):
    # A2, hallazgo 1: el primer intento guarda su archivo y falla al confirmar; antes de que
    # borre, el reintento con el mismo ``id`` confirma. El borrado tardío no toca al ganador.
    # Como R2 (``file_overwrite=True``), el almacén escribe sobre una clave que ya existe.
    monkeypatch.setattr(almacen, "get_available_name", lambda nombre, max_length=None: nombre)
    enviados = datos()
    guardar, confirmar, borrar = almacen.save, connection.savepoint_commit, almacen.delete
    estado = {"guardo": False, "fallo": False, "reintento": None}

    def guardar_y_marcar(nombre, contenido, **kwargs):
        estado["guardo"] = True
        return guardar(nombre, contenido, **kwargs)

    def fallar_despues_de_guardar(sid):
        if estado["guardo"] and not estado["fallo"]:
            estado["fallo"] = True
            raise DatabaseError("se cayó la base al confirmar")
        return confirmar(sid)

    def reintentar_y_luego_borrar(nombre):
        if estado["reintento"] is None:
            estado["reintento"] = servicios.enviar_sesion(docente, enviados, pdf())
        return borrar(nombre)

    monkeypatch.setattr(almacen, "save", guardar_y_marcar)
    monkeypatch.setattr(connection, "savepoint_commit", fallar_despues_de_guardar)
    monkeypatch.setattr(almacen, "delete", reintentar_y_luego_borrar)

    with pytest.raises(DatabaseError):
        servicios.enviar_sesion(docente, enviados, pdf())

    monkeypatch.undo()
    ganadora = Sesion.objects.get()
    assert ganadora.pk == estado["reintento"].pk
    assert almacen.exists(ganadora.archivo_clave)
    assert almacen.listdir("sesiones")[1] == [ganadora.archivo_clave.removeprefix("sesiones/")]


def test_cada_intento_tiene_su_propia_clave(docente, datos, almacen, monkeypatch):
    # D4: la clave se conoce antes de escribir y no se repite entre intentos del mismo ``id``.
    enviados = datos()
    claves = []
    guardar = almacen.save

    def fallar_la_primera(nombre, contenido, **kwargs):
        claves.append(nombre)
        if len(claves) == 1:
            raise OSError("R2 no responde")
        return guardar(nombre, contenido, **kwargs)

    monkeypatch.setattr(almacen, "save", fallar_la_primera)
    with pytest.raises(OSError):
        servicios.enviar_sesion(docente, enviados, pdf())

    sesion = servicios.enviar_sesion(docente, enviados, pdf())

    assert len(claves) == 2
    assert claves[0] != claves[1]
    assert sesion.archivo_clave == claves[1]


# --- Envío repetido (D5) ---------------------------------------------------------------------


def test_envio_repetido_con_el_mismo_id_da_el_mismo_exito_sin_escribir_otra_vez(
    docente, datos, almacen, monkeypatch
):
    # Escenario «Se guardó pero no llegó la respuesta».
    enviados = datos()
    primera = servicios.enviar_sesion(docente, enviados, pdf())
    guardados = []
    monkeypatch.setattr(almacen, "save", lambda *a, **k: guardados.append(a))

    segunda = servicios.enviar_sesion(docente, enviados, pdf())

    assert segunda.pk == primera.pk
    assert segunda.compartida == primera.compartida
    assert Sesion.objects.count() == 1
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).count() == 1
    assert not guardados


def test_id_de_otra_autora_da_error_general_sin_escribir(docente, otra_docente, datos, almacen):
    enviados = datos()
    ajena = servicios.enviar_sesion(otra_docente, enviados, pdf())

    errores = errores_de(docente, {**enviados, "titulo": "Otra"}, pdf())

    assert errores == {"general": GENERAL}
    assert list(Sesion.objects.all()) == [ajena]
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).count() == 1
    assert almacen.listdir("sesiones")[1] == [ajena.archivo_clave.removeprefix("sesiones/")]


@pytest.mark.parametrize("id_", ["", "abc", "123", "00000000-0000-0000-0000-00000000000g"])
def test_id_mal_formado_da_error_general_sin_escribir(docente, datos, almacen, id_):
    assert errores_de(docente, datos(id=id_), pdf()) == {"general": GENERAL}
    nada_guardado(almacen)


def test_sin_id_da_error_general(docente, datos, almacen):
    enviados = datos()
    del enviados["id"]

    assert errores_de(docente, enviados, pdf()) == {"general": GENERAL}
    nada_guardado(almacen)


# --- Registro de actividad (D10) -------------------------------------------------------------


def test_sesion_enviada_sin_compartir_deja_su_entrada(docente, datos):
    # Escenario «Sesión enviada sin compartir» (spec registro-actividad).
    sesion = servicios.enviar_sesion(docente, datos(), pdf())

    entrada = RegistroActividad.objects.get(operacion=Operacion.SESION_ENVIADA)
    assert entrada.usuario == docente
    assert entrada.entidad == "sesion"
    assert entrada.entidad_id == str(sesion.pk)
    assert entrada.detalle == {"compartida": False}


def test_sesion_compartida_deja_su_entrada_sin_titulo_ni_nombre_de_archivo(docente, datos):
    # Escenario «Sesión compartida»; también es el escenario de SESION_ENVIADA (escenarios.py).
    servicios.enviar_sesion(docente, datos(compartir="on", acepta_terminos="1"), pdf())

    entrada = RegistroActividad.objects.get(operacion=Operacion.SESION_ENVIADA)
    assert entrada.detalle == {"compartida": True}
    texto = str(entrada.detalle)
    assert "Leemos" not in texto
    assert ".pdf" not in texto


def test_envio_rechazado_no_deja_entrada(docente, datos):
    # Escenario «Envío rechazado o repetido».
    with pytest.raises(ValidationError):
        servicios.enviar_sesion(docente, datos(titulo=""), pdf())

    assert not RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).exists()


# --- Datos del formulario (D9) ---------------------------------------------------------------


def test_con_una_seccion_el_grado_viene_con_el_de_ella(docente, seccion):
    # Escenario «Una sección».
    seccion.docente = docente
    seccion.save()

    formulario = servicios.datos_del_formulario(docente)

    assert formulario["grado"] == 2
    assert formulario["ayuda_grado"] == "Grado de tu sección: 2.º A. Puedes cambiarlo."


def test_con_dos_secciones_el_grado_viene_sin_elegir(docente, seccion):
    # Escenario «Varias secciones o ninguna».
    seccion.docente = docente
    seccion.save()
    Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B", docente=docente)

    formulario = servicios.datos_del_formulario(docente)

    assert formulario["grado"] is None
    assert formulario["ayuda_grado"] == "Elige el grado de esta sesión."


def test_sin_seccion_el_grado_viene_sin_elegir(docente):
    formulario = servicios.datos_del_formulario(docente)

    assert formulario["grado"] is None
    assert formulario["ayuda_grado"] == "Elige el grado de esta sesión."


def test_una_seccion_de_un_anio_cerrado_no_cuenta(docente, institucion, seccion):
    cerrado = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    Seccion.objects.create(anio_escolar=cerrado, grado=5, nombre="A", docente=docente)

    assert servicios.datos_del_formulario(docente)["grado"] is None


def test_los_grados_son_de_1_a_6(docente):
    assert servicios.datos_del_formulario(docente)["grados"] == [
        (1, "1.º grado"),
        (2, "2.º grado"),
        (3, "3.º grado"),
        (4, "4.º grado"),
        (5, "5.º grado"),
        (6, "6.º grado"),
    ]


def test_las_areas_son_las_que_trabaja_la_institucion_en_orden_siagie(docente, institucion):
    # Escenario «Áreas de la institución».
    matematica = Area.objects.get(codigo_siagie=MATEMATICA)
    InstitucionArea.objects.filter(institucion=institucion, area=matematica).update(
        se_trabaja=False
    )
    esperadas = list(
        InstitucionArea.objects.filter(institucion=institucion, se_trabaja=True)
        .order_by("area__orden", "area__pk")
        .values_list("area__pk", flat=True)
    )

    areas = servicios.datos_del_formulario(docente)["areas"]

    assert [area.pk for area in areas] == esperadas
    assert matematica not in areas
    assert Area.objects.get(codigo_siagie=COMUNICACION) in areas
    assert [area.orden for area in areas] == sorted(area.orden for area in areas)
