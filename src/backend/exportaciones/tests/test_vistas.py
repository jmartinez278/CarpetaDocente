"""Vistas de completar la plantilla del SIAGIE y corregir su equivalencia (US-024/025, D1, D4, D13).

Specs «Solo la dirección completa la plantilla», «Archivo que no corresponde a la plantilla»,
«Sección de la plantilla», «Sin notas en el periodo», «Resumen del llenado» y «Corregir la
equivalencia». Todos los nombres son ficticios.
"""

import base64
import io
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from openpyxl import load_workbook

from actividad.models import Operacion, RegistroActividad
from exportaciones import servicios
from exportaciones.models import EquivalenciaSeccion
from exportaciones.tests.plantilla import generar
from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.django_db

MARIA = "PÉREZ QUISPE, MARÍA"
URL = "/direccion/plantilla-siagie/"
AVISO_BORRADA = (
    "Quitamos la equivalencia. "
    "La próxima plantilla de 2.º TRIUNFADORES te pedirá elegir la sección."
)


def plantilla(**campos):
    campos.setdefault("nombre_seccion", "A")
    campos.setdefault("nombres", ["PEREZ QUISPE, MARIA"])
    campos.setdefault("hojas", {"063-MATE": 4})
    return generar(**campos)


def subir(client, contenido=None, nombre="RegNotas_2_A_B3.xlsx", **datos):
    archivo = SimpleUploadedFile(nombre, plantilla() if contenido is None else contenido)
    return client.post(URL, {"archivo": archivo, **datos})


@pytest.fixture
def cliente(client, direccion):
    client.force_login(direccion)
    return client


def completadas():
    return RegistroActividad.objects.filter(operacion=Operacion.PLANTILLA_SIAGIE_COMPLETADA)


# --- Solo la dirección completa la plantilla ---


def test_la_docente_va_a_su_inicio_y_no_se_procesa_nada(client, docente, notas_b3):
    client.force_login(docente)

    respuesta = subir(client)

    assert (respuesta.status_code, respuesta.url) == (302, reverse("docente:portada"))
    assert not completadas().exists()


def test_el_administrador_va_a_su_inicio_y_no_se_procesa_nada(client, administrador, notas_b3):
    client.force_login(administrador)

    respuesta = subir(client)

    assert (respuesta.status_code, respuesta.url) == (302, reverse("admin:index"))
    assert not completadas().exists()


def test_sin_sesion_va_al_ingreso(client, notas_b3):
    respuesta = subir(client)

    assert (respuesta.status_code, respuesta.url) == (302, f"{reverse('ingresar')}?next={URL}")
    assert not completadas().exists()


def test_get_responde_405_sin_entrada(cliente, notas_b3):
    assert cliente.get(URL).status_code == 405
    assert not completadas().exists()


def test_la_ruta_se_llama_desde_su_namespace():
    assert reverse("plantilla_siagie:completar") == URL


# --- Resumen y paso de la sección ---


def test_completa_y_responde_el_resumen_con_el_archivo_en_base64(cliente, notas_b3):
    respuesta = subir(cliente)

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert 'data-paso="resumen"' in html
    assert "Plantilla completada" in html
    assert 'download="RegNotas_2_A_B3.xlsx"' in html
    crudo = html.split('data-archivo="', 1)[1].split('"', 1)[0]
    libro = load_workbook(io.BytesIO(base64.b64decode(crudo)))
    assert libro["063-MATE"]["D3"].value == "B"
    assert completadas().count() == 1


def test_el_nombre_de_descarga_queda_sin_ruta(cliente, notas_b3):
    html = subir(cliente, nombre="../../C:\\privado\\RegNotas.xlsx").content.decode()

    assert 'download="RegNotas.xlsx"' in html
    assert "privado" not in html


def test_el_resumen_no_se_guarda_en_cache(cliente, notas_b3):
    assert "no-store" in subir(cliente)["Cache-Control"]


def test_pide_elegir_la_seccion_cuando_el_nombre_no_coincide(cliente, b_con_notas):
    respuesta = subir(cliente, plantilla(nombre_seccion="TRIUNFADORES"))

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert 'data-paso="seccion"' in html
    assert "2.º TRIUNFADORES" in html
    for seccion in Seccion.objects.filter(grado=2):
        assert f'value="{seccion.pk}"' in html
    assert not completadas().exists()
    assert not EquivalenciaSeccion.objects.exists()


def test_guardar_y_completar_envia_la_seccion_elegida(cliente, b_con_notas):
    respuesta = subir(cliente, plantilla(nombre_seccion="TRIUNFADORES"), seccion=b_con_notas.pk)

    assert respuesta.status_code == 200
    assert 'data-paso="resumen"' in respuesta.content.decode()
    assert EquivalenciaSeccion.objects.get().seccion == b_con_notas


def test_el_resumen_con_equivalencia_ofrece_corregirla(cliente, b_con_notas):
    html = subir(cliente, plantilla(nombre_seccion="TRIUNFADORES"), seccion=b_con_notas.pk)
    html = html.content.decode()

    equivalencia = EquivalenciaSeccion.objects.get()
    assert reverse("plantilla_siagie:borrar", args=[equivalencia.pk]) in html
    assert "¿No es esta sección?" in html


def test_el_resumen_por_nombre_no_ofrece_corregir(cliente, notas_b3):
    html = subir(cliente).content.decode()

    assert "¿No es esta sección?" not in html


def test_los_nombres_no_encontrados_van_escapados(cliente, notas_b3):
    nombres = ["PEREZ QUISPE, MARIA", "<script>alert(1)</script>, X"]

    html = subir(cliente, plantilla(nombres=nombres)).content.decode()

    assert "&lt;script&gt;alert(1)&lt;/script&gt;, X" in html
    assert "<script>alert(1)" not in html


# --- Rechazos en JSON (400) ---


def error_de(respuesta):
    assert respuesta.status_code == 400
    assert respuesta["Content-Type"].startswith("application/json")
    return json.loads(respuesta.content)


def test_mas_de_3_mb_tiene_su_propio_mensaje(cliente, notas_b3):
    """3 MB: en base64 la completada aún cabe en los 4,5 MB de una respuesta de Vercel."""
    cuerpo = error_de(subir(cliente, b"0" * (3 * 1024 * 1024 + 1)))

    assert cuerpo == {
        "error": "El archivo supera los 3 MB. Elige uno más pequeño.",
        "ayuda_siagie": False,
    }


def test_una_completada_que_no_cabe_en_la_respuesta_es_un_400(cliente, notas_b3, monkeypatch):
    monkeypatch.setattr(
        servicios.siagie.Libro, "guardar", lambda libro: b"0" * (3 * 1024 * 1024 + 1)
    )

    cuerpo = error_de(subir(cliente, plantilla()))

    assert cuerpo == {
        "error": "La plantilla completada supera los 3 MB y no se puede descargar. "
        "No se guardó ningún cambio.",
        "ayuda_siagie": False,
    }
    assert not completadas().exists()


@pytest.mark.parametrize("contenido", [b"%PDF-1.4 no es un libro", b""])
def test_un_archivo_que_no_es_la_plantilla_lleva_la_ayuda_del_siagie(cliente, notas_b3, contenido):
    cuerpo = error_de(subir(cliente, contenido))

    assert cuerpo == {
        "error": "El archivo no corresponde a la plantilla de notas del SIAGIE",
        "ayuda_siagie": True,
    }
    assert not completadas().exists()


def test_sin_archivo_es_el_mensaje_de_la_plantilla(cliente, notas_b3):
    cuerpo = error_de(cliente.post(URL, {}))

    assert cuerpo["ayuda_siagie"] is True


def test_otra_institucion_es_el_mensaje_de_la_plantilla(cliente, notas_b3):
    cuerpo = error_de(subir(cliente, plantilla(codigo_modular="0000000")))

    assert cuerpo["ayuda_siagie"] is True


def test_periodo_sin_notas_no_lleva_la_ayuda_del_siagie(cliente, notas_b3):
    cuerpo = error_de(subir(cliente, plantilla(periodo="B4", texto_periodo="CUARTO BIMESTRE")))

    assert cuerpo == {"error": "No hay notas para completar en este periodo", "ayuda_siagie": False}
    assert not completadas().exists()


def test_seccion_no_valida_por_una_peticion_armada_a_mano(cliente, b_con_notas, otra_institucion):
    otro_anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    ajena = Seccion.objects.create(anio_escolar=otro_anio, grado=2, nombre="B")

    cuerpo = error_de(subir(cliente, plantilla(nombre_seccion="TRIUNFADORES"), seccion=ajena.pk))

    assert cuerpo == {
        "error": "La sección elegida no es válida. Elige una de la lista.",
        "ayuda_siagie": False,
    }
    assert not EquivalenciaSeccion.objects.exists()


def test_seccion_con_texto_que_no_es_un_numero_no_es_valida(cliente, b_con_notas):
    cuerpo = error_de(subir(cliente, plantilla(nombre_seccion="TRIUNFADORES"), seccion="abc"))

    assert cuerpo["error"] == "La sección elegida no es válida. Elige una de la lista."


def test_sin_secciones_del_grado(cliente, notas_b3):
    cuerpo = error_de(subir(cliente, plantilla(grado="TERCERO")))

    assert cuerpo == {
        "error": "Tu I.E. no tiene secciones de 3.º grado en 2027.",
        "ayuda_siagie": False,
    }


def test_sin_opciones_libres_tiene_un_mensaje_propio(cliente, b_con_notas):
    for seccion in Seccion.objects.filter(grado=2):
        EquivalenciaSeccion.objects.create(
            seccion=seccion,
            anio_escolar=seccion.anio_escolar,
            grado=2,
            codigo_siagie="09",
            nombre_siagie=f"OTRA{seccion.pk}",
        )

    cuerpo = error_de(subir(cliente, plantilla(nombre_seccion="NUEVA")))

    assert cuerpo == {
        "error": "Todas las secciones de 2.º grado ya tienen otra equivalencia del SIAGIE.",
        "ayuda_siagie": False,
    }


# --- Recargar el resumen ---


def test_recargar_el_resumen_muestra_el_inicio_sin_completar_otra_vez(cliente, notas_b3):
    subir(cliente)
    assert completadas().count() == 1

    recarga = cliente.get(reverse("direccion:inicio"))

    assert recarga.status_code == 200
    assert 'data-paso="resumen"' not in recarga.content.decode()
    assert completadas().count() == 1


# --- Corregir la equivalencia (D13) ---


def borrar_url(pk):
    return reverse("plantilla_siagie:borrar", args=[pk])


@pytest.fixture
def equivalencia(b_con_notas, direccion):
    servicios.completar_plantilla(
        direccion, plantilla(nombre_seccion="TRIUNFADORES"), b_con_notas.pk
    )
    return EquivalenciaSeccion.objects.get()


def borradas():
    return RegistroActividad.objects.filter(operacion=Operacion.EQUIVALENCIA_SECCION_BORRADA)


def test_la_ruta_de_borrar_tiene_su_forma():
    assert borrar_url(7) == "/direccion/plantilla-siagie/equivalencias/7/borrar/"


def test_borrar_con_js_responde_el_aviso_sin_descarga(cliente, equivalencia):
    respuesta = cliente.post(borrar_url(equivalencia.pk), HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert AVISO_BORRADA in html
    assert "Subir plantilla otra vez" in html
    assert "Descargar plantilla" not in html
    assert not EquivalenciaSeccion.objects.exists()
    assert borradas().count() == 1


def test_borrar_con_htmx_tambien_responde_el_aviso(cliente, equivalencia):
    respuesta = cliente.post(borrar_url(equivalencia.pk), HTTP_HX_REQUEST="true")

    assert respuesta.status_code == 200
    assert AVISO_BORRADA in respuesta.content.decode()


def test_borrar_sin_js_redirige_con_303_al_inicio(cliente, equivalencia):
    respuesta = cliente.post(borrar_url(equivalencia.pk))

    assert (respuesta.status_code, respuesta.url) == (303, reverse("direccion:inicio"))
    assert not EquivalenciaSeccion.objects.exists()


def test_borrar_la_de_otra_institucion_da_404_sin_borrar(cliente, otra_institucion):
    otro_anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    seccion = Seccion.objects.create(anio_escolar=otro_anio, grado=2, nombre="B")
    ajena = EquivalenciaSeccion.objects.create(
        seccion=seccion, anio_escolar=otro_anio, grado=2, codigo_siagie="01", nombre_siagie="X"
    )

    respuesta = cliente.post(borrar_url(ajena.pk))

    assert respuesta.status_code == 404
    assert "Esta equivalencia ya no existe." in respuesta.content.decode()
    assert EquivalenciaSeccion.objects.filter(pk=ajena.pk).exists()
    assert not borradas().exists()


def test_borrar_una_ya_borrada_da_404_sin_entrada_nueva(cliente, equivalencia):
    pk = equivalencia.pk
    cliente.post(borrar_url(pk))

    respuesta = cliente.post(borrar_url(pk))

    assert respuesta.status_code == 404
    assert "Esta equivalencia ya no existe." in respuesta.content.decode()
    assert borradas().count() == 1


def test_docente_y_administrador_van_a_su_inicio_sin_borrar(
    client, docente, administrador, equivalencia
):
    for usuario, inicio in ((docente, "docente:portada"), (administrador, "admin:index")):
        client.force_login(usuario)
        respuesta = client.post(borrar_url(equivalencia.pk))
        assert (respuesta.status_code, respuesta.url) == (302, reverse(inicio))
    assert EquivalenciaSeccion.objects.filter(pk=equivalencia.pk).exists()
    assert not borradas().exists()


def test_borrar_sin_sesion_va_al_ingreso(client, equivalencia):
    respuesta = client.post(borrar_url(equivalencia.pk))

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("ingresar"))
    assert EquivalenciaSeccion.objects.exists()


def test_borrar_sin_csrf_se_rechaza(direccion, equivalencia):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(direccion)

    respuesta = cliente.post(borrar_url(equivalencia.pk))

    assert respuesta.status_code == 403
    assert EquivalenciaSeccion.objects.exists()


def test_subir_sin_csrf_se_rechaza(direccion, notas_b3):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(direccion)

    assert subir(cliente).status_code == 403
    assert not completadas().exists()


def test_borrar_con_get_responde_405(cliente, equivalencia):
    assert cliente.get(borrar_url(equivalencia.pk)).status_code == 405
    assert EquivalenciaSeccion.objects.exists()
