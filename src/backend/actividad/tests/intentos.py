"""Ayudantes de las pruebas de «sin permiso» (spec acceso-secciones; design de US-004, D3 y D5)."""

from html import unescape

from actividad.models import Operacion, RegistroActividad

SIN_PERMISO = "No tienes permiso para ver esta sección"


def intentos():
    """Las entradas INTENTO_SIN_PERMISO como ``(entidad_id, ruta, motivo)``, en orden."""
    return [
        (e.entidad_id, e.detalle["ruta"], e.detalle["motivo"])
        for e in RegistroActividad.objects.filter(operacion=Operacion.INTENTO_SIN_PERMISO).order_by(
            "pk"
        )
    ]


def motivos():
    """Solo los motivos de las entradas INTENTO_SIN_PERMISO, en orden."""
    return [motivo for *_, motivo in intentos()]


def es_sin_permiso(respuesta):
    """403 de «sin permiso»: la página o, con ``HX-Request``, sin cuerpo y con ``HX-Redirect``."""
    if respuesta.status_code != 403:
        return False
    if respuesta.has_header("HX-Redirect"):
        return respuesta["HX-Redirect"] == "/docente/sin-permiso/" and respuesta.content == b""
    return SIN_PERMISO in unescape(respuesta.content.decode())


def pasar_a_otra_docente(seccion, docente):
    """La sección cambia de docente mientras la pantalla sigue abierta (e2e de US-004, D6).

    ``QuerySet.update()`` salta la regla de «sección ocupada» de ``Seccion.save()``: aquí solo
    se simula que la sección dejó de ser de la docente que la tiene abierta.
    """
    from institucion.models import Seccion

    Seccion.objects.filter(pk=seccion.pk).update(docente=docente)
