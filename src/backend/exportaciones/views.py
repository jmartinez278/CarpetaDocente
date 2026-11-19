"""Vistas de completar la plantilla del SIAGIE y corregir su equivalencia (US-024/025, D1, D4, D13).

Solo leen la petición y llaman a ``exportaciones.servicios``. Son del rol Dirección
(``RolRequeridoMixin``): la docente y el Administrador van a su inicio sin procesar nada y una
visita sin sesión, al ingreso. El archivo vive solo en la memoria de la petición: ni se guarda ni
se registra (Ley 29733), y ninguna respuesta se guarda en caché (lleva nombres de estudiantes).

``POST /direccion/plantilla-siagie/`` responde 200 con el fragmento del paso «Elige la sección»
(``data-paso="seccion"``) o del resumen (``data-paso="resumen"``), o 400 con
``{"error": ..., "ayuda_siagie": bool}``.
"""

import base64
import os

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.views import View

from cuentas.acceso import RolRequeridoMixin, es_htmx
from cuentas.models import Usuario
from exportaciones import servicios

NOMBRE_POR_OMISION = "plantilla.xlsx"
ORDINALES = {1: "Primer", 2: "Segundo", 3: "Tercer", 4: "Cuarto"}


def _sin_cache(respuesta):
    add_never_cache_headers(respuesta)
    return respuesta


def _error(mensaje, ayuda_siagie=False):
    return _sin_cache(JsonResponse({"error": mensaje, "ayuda_siagie": ayuda_siagie}, status=400))


def _nombre_base(archivo):
    """Solo el nombre del archivo subido, sin carpetas de ninguno de los dos sistemas."""
    nombre = os.path.basename(archivo.name.replace("\\", "/")).strip()
    return nombre or NOMBRE_POR_OMISION


def _periodo_texto(plantilla):
    numero = plantilla.periodo.numero
    return f"{ORDINALES[numero]} bimestre {plantilla.anio_escolar.anio}"


def _es_js(request):
    """Lo envía ``plantilla-siagie.js`` (XHR) o HTMX; sin ninguno, es un formulario normal."""
    return es_htmx(request) or request.headers.get("X-Requested-With") == "XMLHttpRequest"


class DireccionMixin(RolRequeridoMixin):
    rol_requerido = Usuario.Rol.DIRECCION


class CompletarPlantillaView(DireccionMixin, View):
    """Reconoce, resuelve la sección y completa la plantilla en una sola petición (D1, D3)."""

    http_method_names = ["post"]

    def post(self, request):
        archivo = request.FILES.get("archivo")
        if archivo is None:
            return _error(servicios.siagie.NO_ES_LA_PLANTILLA, ayuda_siagie=True)
        # Un byte más que el límite basta para que ``siagie.abrir`` lo rechace sin leer todo.
        contenido = archivo.read(servicios.siagie.LIMITE_BYTES + 1)
        # Cada rechazo responde su mensaje fijo, nunca el texto de la excepción (CodeQL).
        try:
            resumen = servicios.completar_plantilla(
                request.user, contenido, request.POST.get("seccion")
            )
        except servicios.ArchivoDemasiadoGrande:
            return _error(servicios.siagie.DEMASIADO_GRANDE)
        except servicios.CompletadaDemasiadoGrande:
            return _error(servicios.COMPLETADA_GRANDE)
        except servicios.PlantillaNoReconocida:
            return _error(servicios.siagie.NO_ES_LA_PLANTILLA, ayuda_siagie=True)
        except servicios.SinSeccionesDelGrado as error:
            return _error(servicios.sin_secciones(error.grado, error.anio))
        except servicios.SeccionNoValida:
            return _error(servicios.SECCION_NO_VALIDA)
        except servicios.SinNotasEnElPeriodo:
            return _error(servicios.SIN_NOTAS)
        except servicios.EligeSeccion as eleccion:
            if not eleccion.opciones:
                grado = eleccion.plantilla.grado
                return _error(
                    f"Todas las secciones de {grado}.º grado ya tienen otra "
                    "equivalencia del SIAGIE."
                )
            plantilla = eleccion.plantilla
            contexto = {
                "grado": plantilla.grado,
                "nombre_siagie": plantilla.parametros.nombre_seccion,
                "periodo_texto": _periodo_texto(plantilla),
                "opciones": eleccion.opciones,
            }
            return _sin_cache(render(request, "exportaciones/_seccion.html", contexto))
        contexto = {
            "resumen": resumen,
            "archivo_base64": base64.b64encode(resumen.contenido).decode("ascii"),
            "nombre_archivo": _nombre_base(archivo),
            "periodo_texto": f"Bimestre {resumen.periodo.numero} · {resumen.anio}",
        }
        return _sin_cache(render(request, "exportaciones/_resumen.html", contexto))


class BorrarEquivalenciaView(DireccionMixin, View):
    """«¿No es esta sección?»: borra la equivalencia de la institución de la dirección (D13)."""

    http_method_names = ["post"]

    def post(self, request, equivalencia_id):
        try:
            equivalencia = servicios.borrar_equivalencia(request.user, equivalencia_id)
        except servicios.EquivalenciaInexistente:
            mensaje = servicios.EQUIVALENCIA_INEXISTENTE
            if not _es_js(request):
                # Sin JS no hay panel que corregir: la página completa con el mensaje.
                return _sin_cache(
                    render(
                        request,
                        "exportaciones/_equivalencia_inexistente.html",
                        {"mensaje": mensaje},
                        status=404,
                    )
                )
            return _sin_cache(HttpResponse(mensaje, content_type="text/plain", status=404))
        if not _es_js(request):
            return HttpResponseRedirect(reverse("direccion:inicio"), status=303)
        contexto = {"grado": equivalencia.grado, "nombre_siagie": equivalencia.nombre_siagie}
        return _sin_cache(render(request, "exportaciones/_equivalencia_borrada.html", contexto))
