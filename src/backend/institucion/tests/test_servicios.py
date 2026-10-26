"""Pruebas de la capa de servicios de institucion (spec asignacion-secciones; D2 y D3)."""

import pytest
from django.core.exceptions import ValidationError

from cuentas.models import Usuario
from institucion import servicios
from institucion.models import Seccion

pytestmark = pytest.mark.django_db

OCUPADA = "La sección ya tiene un docente asignado"
NO_ELEGIBLE = "Elige una docente activa de la institución del año escolar."


def asignar(seccion, docente):
    """Asigna por el ORM, la vía que no pasa por el formulario del panel."""
    seccion.docente = docente
    seccion.save()


def docente_guardado(seccion):
    return Seccion.objects.get(pk=seccion.pk).docente


# --- texto_seccion ---


def test_texto_de_la_seccion_usa_el_ordinal(seccion):
    texto = servicios.texto_seccion(seccion)

    assert texto == "2.º grado, sección A"
    assert "º" in texto
    assert "°" not in texto


def test_la_seccion_se_muestra_con_su_texto(seccion):
    assert str(seccion) == "2.º grado, sección A"


# --- Asignación (escenario "Camino ideal") ---


def test_asignar_una_docente_a_una_seccion_vacia(seccion, docente):
    asignar(seccion, docente)

    assert docente_guardado(seccion) == docente


def test_una_docente_puede_tener_dos_secciones(seccion, docente):
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=3, nombre="B")

    asignar(seccion, docente)
    asignar(otra, docente)

    assert set(docente.secciones.all()) == {seccion, otra}


# --- Una sección con un solo docente (escenario "Caso de error") ---


def test_seccion_ocupada_rechaza_a_otra_docente_por_el_orm(seccion, docente, otra_docente):
    asignar(seccion, docente)

    with pytest.raises(ValidationError) as error:
        asignar(seccion, otra_docente)

    assert error.value.message_dict == {"docente": [OCUPADA]}
    assert docente_guardado(seccion) == docente


def test_seccion_ocupada_rechaza_a_otra_docente_por_la_validacion(seccion, docente, otra_docente):
    asignar(seccion, docente)
    seccion.docente = otra_docente

    with pytest.raises(ValidationError) as error:
        seccion.full_clean()

    assert error.value.message_dict == {"docente": [OCUPADA]}


def test_seccion_ocupada_rechaza_una_copia_desactualizada(seccion, docente, otra_docente):
    """Dos Administradores abren la misma sección vacía; el segundo no pisa al primero."""
    copia = Seccion.objects.get(pk=seccion.pk)
    asignar(seccion, docente)

    with pytest.raises(ValidationError):
        asignar(copia, otra_docente)

    assert docente_guardado(seccion) == docente


def test_guardar_el_mismo_docente_no_da_error(seccion, docente):
    asignar(seccion, docente)
    seccion.nombre = "A"

    seccion.full_clean()
    seccion.save()

    assert docente_guardado(seccion) == docente


def test_crear_una_seccion_con_docente(anio_abierto, docente):
    nueva = Seccion.objects.create(anio_escolar=anio_abierto, grado=1, nombre="A", docente=docente)

    assert docente_guardado(nueva) == docente


# --- Cambio en dos pasos (escenario "Flujo alternativo válido") ---


def test_cambio_de_seccion_en_dos_pasos_conserva_la_original(seccion, docente):
    nueva = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=4, nombre="C")
    asignar(seccion, docente)

    asignar(seccion, None)
    asignar(nueva, docente)

    original = Seccion.objects.get(pk=seccion.pk)
    assert (original.anio_escolar, original.grado, original.nombre) == (
        seccion.anio_escolar,
        2,
        "A",
    )
    assert original.docente is None
    assert list(docente.secciones.all()) == [nueva]


# --- Docentes que se pueden asignar ---


def test_no_se_asigna_una_cuenta_de_la_direccion(seccion, direccion):
    with pytest.raises(ValidationError) as error:
        asignar(seccion, direccion)

    assert error.value.message_dict == {"docente": [NO_ELEGIBLE]}
    assert docente_guardado(seccion) is None


def test_no_se_asigna_una_cuenta_desactivada(seccion, crear_usuario):
    inactiva = crear_usuario("pflores", is_active=False)

    with pytest.raises(ValidationError):
        asignar(seccion, inactiva)

    assert docente_guardado(seccion) is None


def test_no_se_asigna_una_docente_de_otra_institucion(seccion, crear_usuario, otra_institucion):
    ajena = crear_usuario("cvargas", institucion=otra_institucion)

    with pytest.raises(ValidationError):
        asignar(seccion, ajena)

    assert docente_guardado(seccion) is None


def test_no_se_crea_una_seccion_con_una_cuenta_no_elegible(anio_abierto, direccion):
    with pytest.raises(ValidationError):
        Seccion.objects.create(anio_escolar=anio_abierto, grado=1, nombre="A", docente=direccion)

    assert not Seccion.objects.exists()


def test_docente_asignada_y_luego_desactivada_se_conserva(seccion, docente):
    asignar(seccion, docente)
    docente.is_active = False
    docente.save()

    seccion.full_clean()
    seccion.save()

    assert docente_guardado(seccion) == docente


def test_docente_asignada_y_luego_desactivada_se_puede_quitar(seccion, docente):
    asignar(seccion, docente)
    Usuario.objects.filter(pk=docente.pk).update(is_active=False)

    asignar(seccion, None)

    assert docente_guardado(seccion) is None
