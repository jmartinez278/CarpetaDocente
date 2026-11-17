"""Visibilidad, listas y búsqueda de sesiones (specs detalle-sesion y repositorio-sesiones;
design de US-011, D4 y D5).

``sesion_visible`` es la única puerta de la página, la descarga, la vista y las escrituras. Las
listas filtran siempre por la institución de la docente y nunca cargan el texto completo.
"""

import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from catalogo.models import InstitucionArea
from repositorio import servicios
from repositorio.models import TIPO_DOCX, TIPO_PDF, Sesion, SesionVista

pytestmark = pytest.mark.django_db

LIMA = ZoneInfo("America/Lima")


def titulos(pagina):
    return [sesion.titulo for sesion in pagina.sesiones]


# --- Quién ve una sesión (D5) ----------------------------------------------------------------


@pytest.mark.parametrize("compartida", [True, False])
def test_la_autora_ve_su_sesion_compartida_o_no(crear_sesion, docente, compartida):
    sesion = crear_sesion(docente, compartida=compartida)

    assert servicios.sesion_visible(docente, sesion.pk) == sesion


def test_una_colega_ve_la_compartida_de_su_institucion(crear_sesion, docente, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=True)

    assert servicios.sesion_visible(docente, sesion.pk) == sesion


def test_una_colega_no_ve_la_ajena_sin_compartir(crear_sesion, docente, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=False)

    assert servicios.sesion_visible(docente, sesion.pk) is None


def test_una_docente_no_ve_la_compartida_de_otra_institucion(crear_sesion, docente, colega_de_otra):
    sesion = crear_sesion(colega_de_otra, compartida=True)

    assert servicios.sesion_visible(docente, sesion.pk) is None


@pytest.mark.parametrize("id_sesion", [uuid.uuid4(), str(uuid.uuid4()), "no-es-un-uuid", None])
def test_una_inexistente_o_mal_formada_no_es_visible(docente, id_sesion):
    assert servicios.sesion_visible(docente, id_sesion) is None


def test_la_misma_docente_de_otra_institucion_no_ve_su_sesion_por_la_institucion(
    crear_sesion, docente, otra_docente, otra_institucion
):
    # La institución sale de la sesión y de la cuenta, nunca de la petición.
    sesion = crear_sesion(otra_docente, compartida=True)
    Sesion.objects.filter(pk=sesion.pk).update(institucion=otra_institucion)

    assert servicios.sesion_visible(docente, sesion.pk) is None
    assert servicios.sesion_visible(otra_docente, sesion.pk) is not None


# --- Mis sesiones (D5) -----------------------------------------------------------------------


def _lima(dia, hora=10):
    return datetime(dia.year, dia.month, dia.day, hora, tzinfo=LIMA)


def test_mis_sesiones_solo_las_suyas_de_la_mas_reciente_a_la_mas_antigua(
    crear_sesion, docente, otra_docente
):
    ahora = timezone.now()
    crear_sesion(docente, titulo="Antigua", creado_en=ahora - timedelta(hours=3))
    crear_sesion(docente, titulo="Reciente", compartida=True, creado_en=ahora - timedelta(hours=1))
    crear_sesion(otra_docente, titulo="Ajena compartida", compartida=True)
    crear_sesion(otra_docente, titulo="Ajena sin compartir")

    pagina = servicios.mis_sesiones(docente)

    assert titulos(pagina) == ["Reciente", "Antigua"]
    assert pagina.hay_mas is False


def test_mis_sesiones_agrupa_por_dia_en_hora_de_lima(crear_sesion, docente, monkeypatch):
    # Escenario «Agrupadas por día»: hoy es el jueves 5 de noviembre de 2026 en Lima.
    hoy = datetime(2026, 11, 5, 9, tzinfo=LIMA)
    monkeypatch.setattr(timezone, "now", lambda: hoy)
    crear_sesion(docente, titulo="Hoy temprano", creado_en=_lima(hoy, 7))
    crear_sesion(docente, titulo="Hoy más tarde", creado_en=_lima(hoy, 8))
    crear_sesion(docente, titulo="Ayer", creado_en=_lima(hoy - timedelta(days=1), 15))
    crear_sesion(docente, titulo="El lunes", creado_en=datetime(2026, 11, 2, 18, tzinfo=LIMA))
    # 23:30 del 1 de noviembre en Lima es el 2 de noviembre en UTC: va al domingo.
    crear_sesion(
        docente, titulo="Domingo noche", creado_en=datetime(2026, 11, 1, 23, 30, tzinfo=LIMA)
    )

    grupos = servicios.mis_sesiones(docente).grupos

    assert [(etiqueta, [s.titulo for s in sesiones]) for etiqueta, sesiones in grupos] == [
        ("Hoy", ["Hoy más tarde", "Hoy temprano"]),
        ("Ayer", ["Ayer"]),
        ("lun 2 nov", ["El lunes"]),
        ("dom 1 nov", ["Domingo noche"]),
    ]


def test_mis_sesiones_muestra_20_y_ver_mas_trae_las_5_restantes_sin_repetir(crear_sesion, docente):
    # Escenario «Ver más»: 25 sesiones, dos con la misma hora (orden estable por pk).
    ahora = timezone.now()
    for indice in range(25):
        crear_sesion(
            docente, titulo=f"Sesión {indice:02}", creado_en=ahora - timedelta(minutes=indice // 2)
        )

    primera = servicios.mis_sesiones(docente)
    segunda = servicios.mis_sesiones(docente, pagina=2)

    assert len(primera.sesiones) == 20 and primera.hay_mas is True
    assert len(segunda.sesiones) == 5 and segunda.hay_mas is False
    ids = [s.pk for s in primera.sesiones + segunda.sesiones]
    assert len(set(ids)) == 25


@pytest.mark.parametrize("pagina", ["0", "-1", "abc", "", None, "99999999999"])
def test_una_pagina_invalida_es_la_primera(crear_sesion, docente, pagina):
    crear_sesion(docente)

    assert len(servicios.mis_sesiones(docente, pagina=pagina).sesiones) == 1


def test_mis_sesiones_cuenta_las_colegas_que_la_vieron(
    crear_sesion, docente, otra_docente, crear_usuario
):
    vista = crear_sesion(docente, titulo="Vista", compartida=True)
    crear_sesion(docente, titulo="Sin vistas", compartida=True)
    tercera = crear_usuario("jrojas", first_name="Julia")
    SesionVista.objects.create(sesion=vista, usuario=otra_docente)
    SesionVista.objects.create(sesion=vista, usuario=tercera)

    vistas = {s.titulo: s.vistas_total for s in servicios.mis_sesiones(docente).sesiones}

    assert vistas == {"Vista": 2, "Sin vistas": 0}


def test_las_tarjetas_traen_las_primeras_lineas_del_texto(crear_sesion, docente):
    crear_sesion(docente, texto="Inicio de la sesión\n" + "x" * 2000)

    tarjeta = servicios.mis_sesiones(docente).sesiones[0]

    assert tarjeta.inicio_texto.startswith("Inicio de la sesión\n")
    assert len(tarjeta.inicio_texto) == servicios.INICIO_TEXTO


def _columnas_leidas(sql):
    """Las columnas del SELECT, sin lo que va dentro de LEFT(...)."""
    seleccion = sql.split(" FROM ", 1)[0]
    return re.sub(r'LEFT\("sesion"\."texto", \d+\)', "", seleccion)


def test_ninguna_lista_carga_el_texto_completo_y_las_consultas_son_pocas(
    crear_sesion, docente, otra_docente
):
    for indice in range(5):
        crear_sesion(otra_docente, titulo=f"Ajena {indice}", compartida=True, texto="agua " * 50)
        crear_sesion(docente, titulo=f"Propia {indice}", compartida=True, texto="agua " * 50)

    with CaptureQueriesContext(connection) as mis:
        [(s.area.nombre, s.vistas_total) for s in servicios.mis_sesiones(docente).sesiones]
    with CaptureQueriesContext(connection) as repo:
        pagina = servicios.buscar_repositorio(docente, q="agua", grado="2", area="")
        [(s.area.nombre, s.autor.get_full_name()) for s in pagina.sesiones]

    assert len(mis) == 1
    assert len(repo) <= 3
    for consulta in [*mis.captured_queries, *repo.captured_queries]:
        columnas = _columnas_leidas(consulta["sql"])
        assert '"sesion"."texto"' not in columnas
        assert '"sesion"."texto_busqueda"' not in columnas


# --- Repositorio de la institución (D4, D5) --------------------------------------------------


def test_el_repositorio_lista_solo_las_compartidas_de_su_institucion(
    crear_sesion, docente, otra_docente, colega_de_otra
):
    # Escenarios «Compartidas de la institución» y «Otra institución».
    ahora = timezone.now()
    crear_sesion(docente, titulo="Mía", compartida=True, creado_en=ahora - timedelta(hours=1))
    crear_sesion(
        otra_docente, titulo="Colega 1", compartida=True, creado_en=ahora - timedelta(hours=2)
    )
    crear_sesion(otra_docente, titulo="Colega 2", compartida=True, creado_en=ahora)
    crear_sesion(otra_docente, titulo="Sin compartir")
    crear_sesion(docente, titulo="Mía sin compartir")
    crear_sesion(colega_de_otra, titulo="Otra institución", compartida=True)

    pagina = servicios.buscar_repositorio(docente)

    assert titulos(pagina) == ["Colega 2", "Mía", "Colega 1"]
    assert pagina.total == 3


def test_el_repositorio_muestra_20_y_ver_mas_el_resto(crear_sesion, docente, otra_docente):
    for indice in range(22):
        crear_sesion(otra_docente, titulo=f"S{indice}", compartida=True)

    primera = servicios.buscar_repositorio(docente)
    segunda = servicios.buscar_repositorio(docente, pagina="2")

    assert (len(primera.sesiones), primera.hay_mas, primera.total) == (20, True, 22)
    assert (len(segunda.sesiones), segunda.hay_mas) == (2, False)
    assert not {s.pk for s in primera.sesiones} & {s.pk for s in segunda.sesiones}


def test_buscar_sin_distinguir_tildes_ni_mayusculas(crear_sesion, docente, otra_docente):
    # Escenario «Tildes y mayúsculas».
    crear_sesion(
        otra_docente, titulo="Escribimos recomendaciones para cuidar el agua", compartida=True
    )
    crear_sesion(
        otra_docente, titulo="Otra", proposito="Escribir una recomendación", compartida=True
    )
    crear_sesion(otra_docente, titulo="Sumamos fracciones", compartida=True)

    pagina = servicios.buscar_repositorio(docente, q="RECOMENDACION")

    assert sorted(titulos(pagina)) == ["Escribimos recomendaciones para cuidar el agua", "Otra"]
    assert pagina.q == "RECOMENDACION"


def test_buscar_una_palabra_que_solo_esta_en_el_archivo(crear_sesion, docente, otra_docente):
    crear_sesion(
        otra_docente, titulo="Evaluamos", texto="Usamos una Lista de cotejo.", compartida=True
    )
    crear_sesion(otra_docente, titulo="Otra", texto="Nada que ver", compartida=True)

    assert titulos(servicios.buscar_repositorio(docente, q="lista de cotejo")) == ["Evaluamos"]


def test_varias_palabras_deben_estar_todas_en_cualquier_orden(crear_sesion, docente, otra_docente):
    # Escenario «Varias palabras».
    crear_sesion(
        otra_docente, titulo="Cuidamos el agua", proposito="en la escuela", compartida=True
    )
    crear_sesion(otra_docente, titulo="Cuidamos el agua en casa", compartida=True)
    crear_sesion(otra_docente, titulo="La escuela limpia", compartida=True)

    assert titulos(servicios.buscar_repositorio(docente, q="  escuela   AGUA ")) == [
        "Cuidamos el agua"
    ]


@pytest.mark.parametrize("q", ["%", "_", "100%", "a_b"])
def test_los_comodines_se_buscan_como_texto(crear_sesion, docente, otra_docente, q):
    crear_sesion(otra_docente, titulo="Avance al 100% de a_b", compartida=True)
    crear_sesion(otra_docente, titulo="Sin signos", compartida=True)

    assert titulos(servicios.buscar_repositorio(docente, q=q)) == ["Avance al 100% de a_b"]


def test_una_busqueda_de_mas_de_100_caracteres_usa_los_primeros_100(
    crear_sesion, docente, otra_docente
):
    crear_sesion(otra_docente, titulo="x" * 100, compartida=True)

    pagina = servicios.buscar_repositorio(docente, q="x" * 100 + "y")

    assert len(pagina.sesiones) == 1
    assert pagina.q == "x" * 100


def test_una_busqueda_vacia_o_de_espacios_no_filtra(crear_sesion, docente, otra_docente):
    crear_sesion(otra_docente, compartida=True)

    assert servicios.buscar_repositorio(docente, q="   ").total == 1


def test_filtrar_por_grado_y_area(crear_sesion, docente, otra_docente, comunicacion, matematica):
    # Escenario «Camino ideal (grado y área)».
    crear_sesion(otra_docente, titulo="3.º Comunicación", grado=3, compartida=True)
    crear_sesion(otra_docente, titulo="3.º Matemática", grado=3, area=matematica, compartida=True)
    crear_sesion(otra_docente, titulo="2.º Comunicación", grado=2, compartida=True)

    pagina = servicios.buscar_repositorio(docente, grado="3", area=str(comunicacion.pk))

    assert titulos(pagina) == ["3.º Comunicación"]
    assert (pagina.grado, pagina.area) == (3, comunicacion)


@pytest.mark.parametrize("grado", ["7", "0", "-1", "tres", "３", "2.5"])
def test_un_grado_que_no_existe_se_ignora(crear_sesion, docente, otra_docente, grado):
    crear_sesion(otra_docente, compartida=True)

    pagina = servicios.buscar_repositorio(docente, grado=grado)

    assert pagina.total == 1 and pagina.grado is None


def test_un_area_que_la_institucion_no_trabaja_se_ignora(
    crear_sesion, docente, otra_docente, institucion, matematica
):
    InstitucionArea.objects.filter(institucion=institucion, area=matematica).update(
        se_trabaja=False
    )
    crear_sesion(otra_docente, compartida=True)

    for area in [str(matematica.pk), "999999", "abc", "99999999999999"]:
        pagina = servicios.buscar_repositorio(docente, area=area)
        assert pagina.total == 1 and pagina.area is None


# --- Conteos (D5) ----------------------------------------------------------------------------


def test_conteos_por_area_con_las_areas_de_la_institucion_en_orden_siagie(
    crear_sesion, docente, otra_docente, colega_de_otra, institucion, comunicacion, matematica
):
    # Escenario «Conteo por área».
    for _ in range(3):
        crear_sesion(otra_docente, compartida=True)
    for _ in range(2):
        crear_sesion(otra_docente, area=matematica, compartida=True)
    crear_sesion(otra_docente)  # sin compartir: no cuenta
    crear_sesion(colega_de_otra, compartida=True)  # otra institución: no cuenta

    conteos = servicios.conteos_por_area(docente)

    trabajadas = [
        fila.area
        for fila in InstitucionArea.objects.filter(institucion=institucion, se_trabaja=True)
        .select_related("area")
        .order_by("area__orden", "area__pk")
    ]
    assert [area for area, _ in conteos.areas] == trabajadas
    por_area = dict(conteos.areas)
    assert conteos.total == 5
    assert por_area[comunicacion] == 3 and por_area[matematica] == 2
    assert sum(por_area.values()) == 5


def test_conteos_por_area_siguen_la_busqueda_y_el_grado(
    crear_sesion, docente, otra_docente, matematica
):
    crear_sesion(otra_docente, titulo="Agua", grado=3, compartida=True)
    crear_sesion(otra_docente, titulo="Agua", grado=3, area=matematica, compartida=True)
    crear_sesion(otra_docente, titulo="Agua", grado=2, compartida=True)
    crear_sesion(otra_docente, titulo="Fuego", grado=3, compartida=True)

    conteos = servicios.conteos_por_area(docente, q="agua", grado="3")

    assert conteos.total == 2
    assert dict(conteos.areas)[matematica] == 1


def test_los_contadores_de_las_pestanas_son_totales_sin_filtros(
    crear_sesion, docente, otra_docente
):
    # Escenario «Contadores».
    crear_sesion(docente)
    crear_sesion(docente, compartida=True)
    for _ in range(3):
        crear_sesion(otra_docente, compartida=True)
    crear_sesion(otra_docente)

    assert servicios.contadores(docente) == {"mis_sesiones": 2, "repositorio": 4}


def test_un_docx_se_lista_como_word(crear_sesion, docente):
    crear_sesion(docente, tipo_mime=TIPO_DOCX, archivo_nombre="a.docx")

    assert servicios.mis_sesiones(docente).sesiones[0].tipo_corto == "Word"


# --- Colegas que la vieron (D6) --------------------------------------------------------------


def vistas_registradas():
    return list(
        RegistroActividad.objects.filter(operacion=Operacion.SESION_VISTA).values_list(
            "usuario_id", "entidad", "entidad_id", "detalle"
        )
    )


def test_la_primera_vista_de_una_colega_cuenta_y_deja_sesion_vista(
    crear_sesion, docente, otra_docente
):
    # Escenarios «Primera visita de una colega» y «Primera vista».
    sesion = crear_sesion(otra_docente, compartida=True)

    assert servicios.registrar_vista(docente, sesion) is True

    assert SesionVista.objects.filter(sesion=sesion, usuario=docente).count() == 1
    assert vistas_registradas() == [(docente.pk, "sesion", str(sesion.pk), {})]


def test_la_misma_colega_otra_vez_no_cuenta_ni_registra(crear_sesion, docente, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=True)
    servicios.registrar_vista(docente, sesion)

    assert servicios.registrar_vista(docente, sesion) is False

    assert SesionVista.objects.filter(sesion=sesion).count() == 1
    assert len(vistas_registradas()) == 1


def test_la_autora_no_cuenta_ni_registra(crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=True)

    assert servicios.registrar_vista(docente, sesion) is False

    assert not SesionVista.objects.exists()
    assert vistas_registradas() == []


def test_la_vista_de_una_sesion_eliminada_en_el_camino_no_esta_disponible(
    crear_sesion, docente, otra_docente
):
    # La página leyó la sesión y la autora la eliminó antes de contar la vista.
    sesion = crear_sesion(otra_docente, compartida=True)
    Sesion.objects.filter(pk=sesion.pk).delete()

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.registrar_vista(docente, sesion)

    assert not SesionVista.objects.exists()
    assert vistas_registradas() == []


def test_la_vista_de_una_sesion_que_dejo_de_compartirse_en_el_camino_no_cuenta(
    crear_sesion, docente, otra_docente
):
    sesion = crear_sesion(otra_docente, compartida=True)
    Sesion.objects.filter(pk=sesion.pk).update(compartida=False)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.registrar_vista(docente, sesion)

    assert not SesionVista.objects.exists()
    assert vistas_registradas() == []


# --- Entrega del archivo (D6, D7) ------------------------------------------------------------


def descargas():
    return list(
        RegistroActividad.objects.filter(operacion=Operacion.SESION_DESCARGADA)
        .order_by("pk")
        .values_list("usuario_id", "entidad", "entidad_id", "detalle")
    )


def test_descargar_y_ver_dejan_sesion_descargada_con_modo_y_propia(
    con_archivo, docente, otra_docente
):
    # Escenario «Descarga»: una colega descarga y la autora la abre con «Ver».
    nombre = "Sesión 3 – cuento ñandú.pdf"
    sesion = con_archivo(otra_docente, compartida=True, archivo_nombre=nombre)

    descarga = servicios.entregar_archivo(docente, sesion.pk, "descargar")
    vista = servicios.entregar_archivo(otra_docente, sesion.pk, "ver")

    assert descargas() == [
        (docente.pk, "sesion", str(sesion.pk), {"modo": "descargar", "propia": False}),
        (otra_docente.pk, "sesion", str(sesion.pk), {"modo": "ver", "propia": True}),
    ]
    assert descarga.url is None and descarga.archivo.read() == b"%PDF-1.4 cuerpo"
    assert descarga.tipo_mime == TIPO_PDF
    assert descarga.disposicion == (
        "attachment; filename*=utf-8''Sesi%C3%B3n%203%20%E2%80%93%20cuento%20%C3%B1and%C3%BA.pdf"
    )
    assert vista.disposicion.startswith("inline; filename*=utf-8''")
    descarga.archivo.close()
    vista.archivo.close()


def test_un_nombre_ascii_va_entre_comillas(con_archivo, docente):
    sesion = con_archivo(docente, archivo_nombre="leemos.pdf")

    entrega = servicios.entregar_archivo(docente, sesion.pk, "descargar")

    assert entrega.disposicion == 'attachment; filename="leemos.pdf"'
    entrega.archivo.close()


def test_ver_un_word_no_entrega_el_archivo_ni_registra(con_archivo, docente):
    # Escenario «Vista de un Word por su dirección».
    sesion = con_archivo(docente, tipo_mime=TIPO_DOCX, archivo_nombre="a.docx")

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.entregar_archivo(docente, sesion.pk, "ver")

    assert descargas() == []


def test_un_word_se_descarga(con_archivo, docente):
    sesion = con_archivo(docente, tipo_mime=TIPO_DOCX, archivo_nombre="a.docx")

    entrega = servicios.entregar_archivo(docente, sesion.pk, "descargar")

    assert entrega.tipo_mime == TIPO_DOCX
    entrega.archivo.close()


@pytest.mark.parametrize("caso", ["ajena sin compartir", "otra institución", "inexistente"])
def test_una_sesion_no_visible_no_se_entrega_ni_registra(
    con_archivo, docente, otra_docente, colega_de_otra, caso
):
    # Escenario «Descarga rechazada».
    id_sesion = {
        "ajena sin compartir": lambda: con_archivo(otra_docente).pk,
        "otra institución": lambda: con_archivo(colega_de_otra, compartida=True).pk,
        "inexistente": uuid.uuid4,
    }[caso]()

    for modo in ("descargar", "ver"):
        with pytest.raises(servicios.SesionNoDisponible):
            servicios.entregar_archivo(docente, id_sesion, modo)

    assert descargas() == []


def test_un_modo_desconocido_es_un_error_de_programacion(con_archivo, docente):
    sesion = con_archivo(docente)

    with pytest.raises(ValueError):
        servicios.entregar_archivo(docente, sesion.pk, "borrar")
    assert descargas() == []


def test_si_el_archivo_no_se_puede_abrir_no_queda_entrada(crear_sesion, docente):
    sesion = crear_sesion(docente)  # sin archivo en el almacenamiento

    with pytest.raises(FileNotFoundError):
        servicios.entregar_archivo(docente, sesion.pk, "descargar")
    assert descargas() == []
