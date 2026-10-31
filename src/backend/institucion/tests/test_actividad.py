"""Estudiantes, secciones y demostración en el registro de actividad (design de US-008, D2 y D7).

Escenarios "Estudiante editado", "Comando de consola", "Sección descartada", "La operación falla"
y "Una lectura no deja entrada" del spec registro-actividad. Las operaciones de la docente van por
sus vistas; las de consola, por los comandos.
"""

import datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from asistencia import servicios as asistencia
from asistencia.models import Asistencia, Jornada
from institucion import servicios
from institucion.models import Estudiante, Seccion

pytestmark = pytest.mark.django_db

MIERCOLES = datetime.date(2026, 10, 28)


@pytest.fixture
def seccion_docente(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def cliente(client, docente, seccion_docente):
    client.force_login(docente)
    return client


@pytest.fixture
def estudiante(seccion_docente):
    return Estudiante.objects.create(
        seccion=seccion_docente, apellidos="QUISPE MAMANI", nombres="ANA"
    )


@pytest.fixture(autouse=True)
def demo_clave(monkeypatch, clave):
    monkeypatch.setenv("DEMO_CLAVE", clave)


def entradas(operacion):
    return list(RegistroActividad.objects.filter(operacion=operacion).order_by("id"))


def sin_sesion():
    """Las entradas de esta prueba, sin las de iniciar sesión."""
    return list(RegistroActividad.objects.exclude(operacion=Operacion.INICIO_SESION))


def url(nombre, seccion, *argumentos):
    return reverse(f"estudiantes:{nombre}", args=[seccion.pk, *argumentos])


def correr(comando, **opciones):
    call_command(comando, stdout=StringIO(), **opciones)


def con_asistencia(estudiante, docente):
    jornada = Jornada.objects.create(
        seccion=estudiante.seccion, fecha=timezone.localdate(), registrado_por=docente
    )
    Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")
    return jornada


# --- Desde las vistas de la docente ---


def test_importar_deja_estudiantes_importados_con_la_cantidad(cliente, docente, seccion_docente):
    cliente.post(url("pegar", seccion_docente), {"lista": "QUISPE MAMANI, ANA\nROJAS HUAMÁN, LUIS"})

    (entrada,) = entradas(Operacion.ESTUDIANTES_IMPORTADOS)
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(seccion_docente.pk))
    assert entrada.detalle == {"cantidad": 2}


def test_importar_con_errores_no_deja_entrada(cliente, seccion_docente):
    cliente.post(url("pegar", seccion_docente), {"lista": "SOLO APELLIDOS SIN COMA"})

    assert sin_sesion() == []


def test_agregar_deja_estudiante_agregado(cliente, docente, seccion_docente):
    cliente.post(url("agregar", seccion_docente), {"apellidos": "ROJAS HUAMÁN", "nombres": "LUIS"})

    nuevo = Estudiante.objects.get()
    (entrada,) = entradas(Operacion.ESTUDIANTE_AGREGADO)
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("estudiante", str(nuevo.pk))
    assert entrada.detalle == {}


def test_agregar_repetido_no_deja_entrada(cliente, estudiante, seccion_docente):
    cliente.post(url("agregar", seccion_docente), {"apellidos": "QUISPE MAMANI", "nombres": "ANA"})

    assert sin_sesion() == []


def test_editar_deja_estudiante_editado_sin_los_nombres(
    cliente, docente, estudiante, seccion_docente
):
    cliente.post(
        url("editar", seccion_docente, estudiante.pk),
        {"apellidos": "QUISPE MAMANÍ", "nombres": "ANA"},
    )

    (entrada,) = entradas(Operacion.ESTUDIANTE_EDITADO)
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("estudiante", str(estudiante.pk))
    assert entrada.detalle == {"campos": ["apellidos"]}
    texto = str(entrada.detalle)
    for nombre in ("QUISPE", "MAMANI", "MAMANÍ", "ANA"):
        assert nombre not in texto


def test_editar_sin_cambios_no_deja_entrada(cliente, estudiante, seccion_docente):
    cliente.post(
        url("editar", seccion_docente, estudiante.pk),
        {"apellidos": "QUISPE MAMANI", "nombres": "ANA"},
    )

    assert sin_sesion() == []


def test_editar_con_una_copia_vieja_deja_estudiante_editado(docente, estudiante):
    """Otra pestaña cambió los apellidos: volver a los de la copia vieja también es un cambio."""
    vieja = Estudiante.objects.get(pk=estudiante.pk)
    servicios.editar_estudiante(estudiante, "QUISPE MAMANÍ", "ANA", usuario=docente)

    servicios.editar_estudiante(vieja, "QUISPE MAMANI", "ANA", usuario=docente)

    estudiante.refresh_from_db()
    assert estudiante.apellidos == "QUISPE MAMANI"
    assert [entrada.detalle for entrada in entradas(Operacion.ESTUDIANTE_EDITADO)] == [
        {"campos": ["apellidos"]},
        {"campos": ["apellidos"]},
    ]


def test_quitar_deja_estudiante_quitado(cliente, docente, estudiante, seccion_docente):
    cliente.post(url("quitar", seccion_docente, estudiante.pk))

    (entrada,) = entradas(Operacion.ESTUDIANTE_QUITADO)
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("estudiante", str(estudiante.pk))


def test_vaciar_deja_lista_vaciada_con_la_cantidad(cliente, docente, estudiante, seccion_docente):
    Estudiante.objects.create(seccion=seccion_docente, apellidos="ROJAS HUAMÁN", nombres="LUIS")

    cliente.post(url("vaciar", seccion_docente))

    (entrada,) = entradas(Operacion.LISTA_VACIADA)
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(seccion_docente.pk))
    assert entrada.detalle == {"cantidad": 2}


def test_vaciar_una_lista_ya_vacia_no_deja_entrada(cliente, seccion_docente):
    cliente.post(url("vaciar", seccion_docente))

    assert entradas(Operacion.LISTA_VACIADA) == []


def test_quitar_bloqueado_por_registros_no_deja_entrada(cliente, docente, estudiante):
    con_asistencia(estudiante, docente)

    cliente.post(url("quitar", estudiante.seccion, estudiante.pk))

    assert Estudiante.objects.filter(pk=estudiante.pk).exists()
    assert entradas(Operacion.ESTUDIANTE_QUITADO) == []


def test_vaciar_bloqueado_por_registros_no_deja_entrada(cliente, docente, estudiante):
    con_asistencia(estudiante, docente)

    cliente.post(url("vaciar", estudiante.seccion))

    assert Estudiante.objects.filter(pk=estudiante.pk).exists()
    assert entradas(Operacion.LISTA_VACIADA) == []


def test_si_falla_el_registro_el_estudiante_no_se_agrega(seccion_docente, docente, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("registro caído")

    monkeypatch.setattr(servicios, "registrar", falla)

    with pytest.raises(RuntimeError):
        servicios.agregar_estudiante(seccion_docente, "ROJAS HUAMÁN", "LUIS", usuario=docente)

    assert not Estudiante.objects.exists()


def test_abrir_la_lista_de_estudiantes_no_deja_entrada(cliente, estudiante, seccion_docente):
    respuesta = cliente.get(url("lista", seccion_docente))

    assert respuesta.status_code == 200
    assert sin_sesion() == []


# --- Comandos de consola: usuario vacío ---


def test_cargar_secciones_deja_seccion_creada_por_seccion_nueva(institucion):
    correr("cargar_secciones", anio=2027, institucion=institucion.pk)

    creadas = entradas(Operacion.SECCION_CREADA)
    assert len(creadas) == 24
    assert {e.entidad_id for e in creadas} == {
        str(pk) for pk in Seccion.objects.values_list("pk", flat=True)
    }
    assert all(e.usuario is None and e.entidad == "seccion" for e in creadas)
    (anio,) = entradas(Operacion.ANIO_CREADO)
    assert anio.usuario is None


def test_cargar_secciones_otra_vez_no_deja_entradas(institucion):
    correr("cargar_secciones", anio=2027, institucion=institucion.pk)
    antes = RegistroActividad.objects.count()

    correr("cargar_secciones", anio=2027, institucion=institucion.pk)

    assert RegistroActividad.objects.count() == antes


@pytest.fixture
def anio_actual(institucion):
    anio_escolar, _, _ = servicios.cargar_secciones(institucion, timezone.localdate().year)
    return anio_escolar


def test_cargar_demo_deja_demo_cargada_con_usuario_vacio_y_conteos(institucion, anio_actual):
    correr("cargar_demo", institucion=institucion.pk, estudiantes=3, confirmar=True)

    (entrada,) = entradas(Operacion.DEMO_CARGADA)
    assert entrada.usuario is None
    assert (entrada.entidad, entrada.entidad_id) == ("anio_escolar", str(anio_actual.pk))
    assert entrada.detalle["secciones"] == 8
    assert entrada.detalle["estudiantes"] == 3
    assert entrada.detalle["dias"] >= 1
    # La carga se registra como una sola operación, no como importaciones sueltas.
    assert entradas(Operacion.ESTUDIANTES_IMPORTADOS) == []


def test_quitar_demo_deja_demo_quitada_con_usuario_vacio_y_conteos(institucion, anio_actual):
    correr("cargar_demo", institucion=institucion.pk, estudiantes=3, confirmar=True)
    dias = entradas(Operacion.DEMO_CARGADA)[0].detalle["dias"]

    correr("quitar_demo", confirmar=True)

    (entrada,) = entradas(Operacion.DEMO_QUITADA)
    assert entrada.usuario is None
    assert entrada.detalle == {
        "secciones": 8,
        "cuentas": 8,
        "estudiantes": 24,
        "jornadas": 8 * dias,
        "estados": 24 * dias,
    }


def test_quitar_demo_sin_demo_no_deja_entrada(db):
    correr("quitar_demo", confirmar=True)

    assert entradas(Operacion.DEMO_QUITADA) == []


def test_descartar_seccion_deja_seccion_descartada_y_conserva_la_asistencia(anio_actual, docente):
    seccion = Seccion.objects.get(anio_escolar=anio_actual, grado=3, nombre="A")
    seccion.docente = docente
    seccion.save()
    estudiante = Estudiante.objects.create(seccion=seccion, apellidos="QUISPE", nombres="ANA")
    # Toque real (miércoles fijo): deja REGISTRO_ASISTENCIA y ASISTENCIA_CAMBIADA.
    asistencia.marcar(seccion, estudiante.pk, MIERCOLES, "ASISTIO", "", docente, hoy=MIERCOLES)
    de_asistencia = list(
        RegistroActividad.objects.filter(
            operacion__in=[Operacion.REGISTRO_ASISTENCIA, Operacion.ASISTENCIA_CAMBIADA]
        ).values_list("pk", flat=True)
    )

    correr("descartar_seccion", seccion=seccion.pk, confirmar=True)

    (entrada,) = entradas(Operacion.SECCION_DESCARTADA)
    assert entrada.usuario is None
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(seccion.pk))
    assert entrada.detalle == {"estudiantes": 1, "jornadas": 1, "estados": 1}
    # Conservación: las entradas de asistencia de la sección descartada siguen.
    assert not Jornada.objects.filter(seccion=seccion).exists()
    assert (
        list(RegistroActividad.objects.filter(pk__in=de_asistencia).values_list("pk", flat=True))
        == de_asistencia
    )
