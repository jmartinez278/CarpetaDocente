"""Ficha del panel para las sesiones de referencia (spec material-referencia; design de US-018,
D4 y D5).

Todo pasa por las pantallas del panel con el Administrador ficticio; las reglas las prueba
``test_servicios_referencia.py``.
"""

import pytest
from django.contrib.admin.models import DELETION, LogEntry
from django.core.files.storage import storages
from django.urls import reverse

from actividad.models import Operacion, RegistroActividad
from actividad.tests.conftest import entrar
from institucion.models import Institucion
from repositorio import servicios
from repositorio.models import Sesion
from repositorio.tests.archivos import pdf, subido

pytestmark = pytest.mark.django_db

LISTA = "admin:repositorio_sesionreferencia_changelist"
AGREGAR = "admin:repositorio_sesionreferencia_add"
FICHA = "admin:repositorio_sesionreferencia_change"
BORRAR = "admin:repositorio_sesionreferencia_delete"
PERMISO = "Uso libre con fines educativos, citando la fuente."


@pytest.fixture
def panel(client, administrador):
    return entrar(client, administrador)


@pytest.fixture
def ficha(institucion, comunicacion):
    """Lo que manda la ficha nueva: «Leemos un cuento», 3.º a 5.º grado, Comunicación."""

    def armar(**cambios):
        valores = {
            "institucion": institucion.pk,
            "grado": "3",
            "grado_hasta": "5",
            "area": comunicacion.pk,
            "titulo": "Leemos un cuento",
            "proposito": "",
            "fuente": "Equipo del proyecto",
            "permiso_uso": PERMISO,
            "archivo": pdf("Leemos un cuento.pdf"),
            "_save": "Guardar",
            **cambios,
        }
        return {clave: valor for clave, valor in valores.items() if valor is not None}

    return armar


@pytest.fixture
def referencia(administrador, institucion, comunicacion):
    datos = {
        "institucion": str(institucion.pk),
        "grado": "3",
        "grado_hasta": "5",
        "area": str(comunicacion.pk),
        "titulo": "Leemos un cuento",
        "proposito": "",
        "fuente": "Equipo del proyecto",
        "permiso_uso": PERMISO,
    }
    sesion = servicios.cargar_referencia(administrador, datos, pdf())
    RegistroActividad.objects.all().delete()
    return sesion


def ficha_de(sesion, **cambios):
    valores = {
        "grado": sesion.grado,
        "grado_hasta": sesion.grado_hasta,
        "area": sesion.area_id,
        "titulo": sesion.titulo,
        "proposito": sesion.proposito,
        "fuente": sesion.fuente,
        "permiso_uso": sesion.permiso_uso,
        "_save": "Guardar",
        **cambios,
    }
    return valores


def errores_de(respuesta):
    return respuesta.context["adminform"].form.errors


def operaciones():
    return list(RegistroActividad.objects.values_list("operacion", flat=True))


# --- Cargar ---------------------------------------------------------------------------------


def test_cargar_desde_la_ficha_con_archivo(panel, administrador, ficha):
    # Escenario «Camino ideal».
    respuesta = panel.post(reverse(AGREGAR), ficha())

    assert respuesta.status_code == 302
    sesion = Sesion.objects.get()
    assert sesion.origen == Sesion.Origen.REFERENCIA
    assert sesion.autor is None
    assert sesion.subido_por == administrador
    assert (sesion.grado, sesion.grado_hasta) == (3, 5)
    assert sesion.archivo_nombre == "Leemos un cuento.pdf"
    assert storages["sesiones"].exists(sesion.archivo_clave)
    assert operaciones() == [Operacion.SESION_REFERENCIA_CARGADA]
    assert respuesta.url == reverse(LISTA)


def test_la_ficha_nueva_pide_el_archivo_con_multipart(panel):
    respuesta = panel.get(reverse(AGREGAR))

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert 'enctype="multipart/form-data"' in contenido
    assert 'name="archivo"' in contenido


@pytest.mark.parametrize("cambios", [{"fuente": "  "}, {"permiso_uso": ""}])
def test_sin_fuente_o_permiso_la_ficha_lo_dice(panel, ficha, cambios):
    respuesta = panel.post(reverse(AGREGAR), ficha(**cambios))

    assert respuesta.status_code == 200
    assert respuesta.context["adminform"].form.non_field_errors() == [
        "Indique la fuente y el permiso de uso"
    ]
    assert "Indique la fuente y el permiso de uso" in respuesta.content.decode()
    assert not Sesion.objects.exists()
    assert operaciones() == []


def test_los_errores_de_campo_van_a_su_campo(panel, ficha):
    respuesta = panel.post(
        reverse(AGREGAR),
        ficha(
            grado="5",
            grado_hasta="3",
            titulo="",
            archivo=subido("foto.pdf", b"\x89PNG\r\n\x1a\n"),
        ),
    )

    assert respuesta.status_code == 200
    assert errores_de(respuesta) == {
        "grado_hasta": ["El grado final no puede ser menor que el inicial."],
        "titulo": ["Falta indicar el título."],
        "archivo": ["Este archivo no es PDF ni Word (.docx). Elige otro archivo."],
    }
    assert not Sesion.objects.exists()


def test_sin_archivo_la_ficha_lo_pide(panel, ficha):
    respuesta = panel.post(reverse(AGREGAR), ficha(archivo=None))

    assert errores_de(respuesta) == {"archivo": ["Elige un archivo PDF o Word (.docx)."]}
    assert not Sesion.objects.exists()


def test_con_una_sola_institucion_viene_elegida(panel, institucion):
    respuesta = panel.get(reverse(AGREGAR))

    assert respuesta.context["adminform"].form.initial["institucion"] == institucion.pk


def test_con_varias_instituciones_ninguna_viene_elegida(panel, institucion, otra_institucion):
    respuesta = panel.get(reverse(AGREGAR))

    assert "institucion" not in respuesta.context["adminform"].form.initial
    assert Institucion.objects.count() == 2


# --- Editar ---------------------------------------------------------------------------------


def test_editar_sin_archivo_cambia_los_datos(panel, referencia):
    respuesta = panel.post(
        reverse(FICHA, args=[referencia.pk]), ficha_de(referencia, titulo="Cuidamos el árbol")
    )

    assert respuesta.status_code == 302
    referencia.refresh_from_db()
    assert referencia.titulo == "Cuidamos el árbol"
    assert "cuidamos el arbol" in referencia.texto_busqueda
    (entrada,) = RegistroActividad.objects.all()
    assert entrada.operacion == Operacion.SESION_REFERENCIA_EDITADA
    assert entrada.detalle == {"campos": ["titulo"]}


def test_la_ficha_guardada_no_deja_cambiar_archivo_ni_institucion(
    panel, referencia, otra_institucion
):
    respuesta = panel.get(reverse(FICHA, args=[referencia.pk]))

    contenido = respuesta.content.decode()
    assert 'name="archivo"' not in contenido
    assert 'name="institucion"' not in contenido
    assert referencia.archivo_nombre in contenido

    panel.post(
        reverse(FICHA, args=[referencia.pk]),
        ficha_de(referencia, institucion=otra_institucion.pk, archivo=pdf("otro.pdf")),
    )
    referencia.refresh_from_db()
    assert referencia.institucion_id != otra_institucion.pk
    assert referencia.archivo_nombre != "otro.pdf"


def test_editar_sin_cambios_no_deja_entrada(panel, referencia):
    respuesta = panel.post(reverse(FICHA, args=[referencia.pk]), ficha_de(referencia))

    assert respuesta.status_code == 302
    assert operaciones() == []


def test_borrar_la_fuente_al_editar_la_ficha_lo_dice(panel, referencia):
    respuesta = panel.post(reverse(FICHA, args=[referencia.pk]), ficha_de(referencia, fuente=""))

    assert respuesta.status_code == 200
    assert "Indique la fuente y el permiso de uso" in respuesta.content.decode()
    referencia.refresh_from_db()
    assert referencia.fuente == "Equipo del proyecto"


# --- Eliminar -------------------------------------------------------------------------------


def test_eliminar_pide_confirmacion_y_luego_borra(
    panel, referencia, django_capture_on_commit_callbacks
):
    confirmacion = panel.get(reverse(BORRAR, args=[referencia.pk]))
    assert confirmacion.status_code == 200
    assert Sesion.objects.filter(pk=referencia.pk).exists()

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = panel.post(reverse(BORRAR, args=[referencia.pk]), {"post": "yes"})

    assert respuesta.status_code == 302
    assert not Sesion.objects.filter(pk=referencia.pk).exists()
    assert not storages["sesiones"].exists(referencia.archivo_clave)
    assert operaciones() == [Operacion.SESION_REFERENCIA_ELIMINADA]
    assert LogEntry.objects.filter(action_flag=DELETION).count() == 1


def test_la_lista_no_ofrece_el_borrado_masivo(panel, referencia):
    respuesta = panel.get(reverse(LISTA))

    assert respuesta.status_code == 200
    assert "delete_selected" not in respuesta.content.decode()


def test_el_borrado_masivo_por_post_no_borra(panel, referencia):
    panel.post(
        reverse(LISTA),
        {"action": "delete_selected", "_selected_action": [referencia.pk], "post": "yes"},
    )

    assert Sesion.objects.filter(pk=referencia.pk).exists()
    assert operaciones() == []


# --- Solo las sesiones de referencia en el panel --------------------------------------------


def test_la_sesion_de_una_docente_no_esta_en_la_lista_y_su_ficha_da_404(
    panel, referencia, docente, crear_sesion
):
    de_la_docente = crear_sesion(docente, titulo="Sesión de Ana")

    lista = panel.get(reverse(LISTA))
    assert "Sesión de Ana" not in lista.content.decode()
    assert "Leemos un cuento" in lista.content.decode()

    assert panel.get(reverse(FICHA, args=[de_la_docente.pk])).status_code == 404
    assert panel.get(reverse(BORRAR, args=[de_la_docente.pk])).status_code == 404
    panel.post(reverse(BORRAR, args=[de_la_docente.pk]), {"post": "yes"})
    assert Sesion.objects.filter(pk=de_la_docente.pk).exists()


@pytest.mark.parametrize("rol", ["docente", "direccion"])
@pytest.mark.parametrize("ruta", ["lista", "agregar", "ficha"])
def test_otro_rol_no_entra(client, request, referencia, rol, ruta):
    entrar(client, request.getfixturevalue(rol))
    url = {
        "lista": reverse(LISTA),
        "agregar": reverse(AGREGAR),
        "ficha": reverse(FICHA, args=[referencia.pk]),
    }[ruta]

    respuesta = client.get(url)

    assert respuesta.status_code in (302, 403)
    if respuesta.status_code == 302:
        assert respuesta.url.startswith(reverse("admin:login"))
