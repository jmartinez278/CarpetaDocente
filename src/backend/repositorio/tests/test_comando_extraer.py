"""Comando ``extraer_textos`` (spec repositorio-sesiones, escenario «Sesiones anteriores»;
design de US-011, D3).

Las sesiones enviadas antes de US-011 no tienen texto transcrito: el comando abre su archivo
del almacenamiento y lo llena. Es repetible.
"""

import logging
import uuid
from io import StringIO

import pytest
from django.core.files.storage import storages
from django.core.management import call_command

from actividad.models import RegistroActividad
from repositorio import servicios
from repositorio.models import Sesion
from repositorio.tests.archivos import docx_con_texto, pdf_con_texto, subido

pytestmark = pytest.mark.django_db


def correr():
    salida = StringIO()
    call_command("extraer_textos", stdout=salida)
    return salida.getvalue()


@pytest.fixture
def anterior(docente, comunicacion):
    """Una sesión como las de antes de US-011: sin texto y buscable solo por título y propósito."""

    def crear(titulo, archivo):
        sesion = servicios.enviar_sesion(
            docente,
            {
                "id": str(uuid.uuid4()),
                "grado": "2",
                "area": str(comunicacion.pk),
                "titulo": titulo,
                "proposito": "Que opinen.",
            },
            archivo,
        )
        Sesion.objects.filter(pk=sesion.pk).update(
            texto="", texto_busqueda=servicios.texto_de_busqueda(titulo, "Que opinen.", "")
        )
        return sesion

    return crear


def test_llena_el_texto_de_las_sesiones_anteriores(anterior):
    word = anterior("Leemos un cuento", subido("a.docx", docx_con_texto(["Formamos equipos"])))
    pdf = anterior("Medimos el aula", subido("b.pdf", pdf_con_texto([["Usamos la cinta métrica"]])))

    salida = correr()

    word.refresh_from_db()
    pdf.refresh_from_db()
    assert word.texto == "Formamos equipos"
    assert word.texto_busqueda == "leemos un cuento que opinen. formamos equipos"
    assert pdf.texto == "Usamos la cinta métrica"
    assert pdf.texto_busqueda == "medimos el aula que opinen. usamos la cinta metrica"
    assert "Sesiones sin texto: 2." in salida
    assert "Con texto ahora: 2." in salida


def test_no_toca_las_que_ya_tienen_texto(anterior, monkeypatch):
    con_texto = anterior("Leemos", subido("a.docx", docx_con_texto(["Texto del archivo"])))
    Sesion.objects.filter(pk=con_texto.pk).update(texto="Ya transcrita", texto_busqueda="ya")
    abiertos = []
    almacen = storages["sesiones"]
    abrir = almacen.open
    monkeypatch.setattr(almacen, "open", lambda *a, **k: abiertos.append(a) or abrir(*a, **k))

    salida = correr()

    con_texto.refresh_from_db()
    assert (con_texto.texto, con_texto.texto_busqueda) == ("Ya transcrita", "ya")
    assert not abiertos
    assert "Sesiones sin texto: 0." in salida


def test_una_sin_texto_o_ilegible_queda_sin_texto(anterior):
    escaneada = anterior("Escaneada", subido("a.pdf", pdf_con_texto([[]])))
    rota = anterior("Rota", subido("b.pdf", b"%PDF-1.4\nrota"))

    salida = correr()

    escaneada.refresh_from_db()
    rota.refresh_from_db()
    assert (escaneada.texto, rota.texto) == ("", "")
    assert escaneada.texto_busqueda == "escaneada que opinen."
    assert "Siguen sin texto: 2." in salida


def test_repara_la_busqueda_de_las_que_nacieron_con_el_despliegue_anterior(anterior):
    # El código anterior inserta sin ``texto_busqueda`` (queda vacío) después de la migración:
    # aunque el archivo no dé texto, el título y el propósito deben encontrarse.
    escaneada = anterior("Escaneada", subido("a.pdf", pdf_con_texto([[]])))
    rota = anterior("Rota", subido("b.pdf", b"%PDF-1.4\nrota"))
    perdida = anterior("Perdida", subido("c.pdf", pdf_con_texto([["No se va a leer"]])))
    storages["sesiones"].delete(perdida.archivo_clave)
    Sesion.objects.update(texto_busqueda="")

    correr()

    for sesion, titulo in [(escaneada, "escaneada"), (rota, "rota"), (perdida, "perdida")]:
        sesion.refresh_from_db()
        assert sesion.texto == ""
        assert sesion.texto_busqueda == f"{titulo} que opinen."
    assert Sesion.objects.filter(texto_busqueda__contains="escaneada").exists()


def test_un_archivo_que_falta_no_detiene_a_las_demas(anterior, caplog):
    perdida = anterior("Perdida", subido("a.docx", docx_con_texto(["No se va a leer"])))
    otra = anterior("Otra", subido("b.docx", docx_con_texto(["Formamos equipos"])))
    storages["sesiones"].delete(perdida.archivo_clave)

    with caplog.at_level(logging.WARNING, logger="repositorio.servicios"):
        salida = correr()

    perdida.refresh_from_db()
    otra.refresh_from_db()
    assert perdida.texto == ""
    assert otra.texto == "Formamos equipos"
    assert "No se pudo abrir su archivo: 1." in salida
    assert "Con texto ahora: 1." in salida
    # El aviso nombra la clave, para buscarla en el almacenamiento; no el título.
    avisos = " ".join(registro.getMessage() for registro in caplog.records)
    assert perdida.archivo_clave in avisos
    assert "Perdida" not in avisos


def test_la_segunda_corrida_no_cambia_nada(anterior):
    word = anterior("Leemos un cuento", subido("a.docx", docx_con_texto(["Formamos equipos"])))
    anterior("Escaneada", subido("b.pdf", pdf_con_texto([[]])))
    correr()
    antes = list(Sesion.objects.order_by("pk").values("pk", "texto", "texto_busqueda"))

    salida = correr()

    assert list(Sesion.objects.order_by("pk").values("pk", "texto", "texto_busqueda")) == antes
    word.refresh_from_db()
    assert word.texto == "Formamos equipos"
    assert "Sesiones sin texto: 1." in salida
    assert "Con texto ahora: 0." in salida


def test_no_pisa_el_texto_que_otro_proceso_guardo_mientras_tanto(anterior, monkeypatch):
    sesion = anterior("Leemos", subido("a.docx", docx_con_texto(["Del comando"])))
    extraer = servicios.extraer_texto

    def adelantarse(archivo, tipo_mime):
        Sesion.objects.filter(pk=sesion.pk).update(texto="De otro proceso")
        return extraer(archivo, tipo_mime)

    monkeypatch.setattr(servicios, "extraer_texto", adelantarse)

    correr()

    sesion.refresh_from_db()
    assert sesion.texto == "De otro proceso"


def test_no_deja_entradas_de_actividad_ni_cambia_la_fecha_de_la_sesion(anterior):
    sesion = anterior("Leemos", subido("a.docx", docx_con_texto(["Formamos equipos"])))
    sesion.refresh_from_db()
    entradas = RegistroActividad.objects.count()

    correr()

    actualizada = Sesion.objects.get(pk=sesion.pk)
    assert actualizada.texto == "Formamos equipos"
    assert actualizada.actualizado_en == sesion.actualizado_en
    assert RegistroActividad.objects.count() == entradas
