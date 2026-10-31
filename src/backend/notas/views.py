"""Vistas de las competencias de una sección (design de US-029, D8).

Solo leen la petición y llaman a ``notas.servicios``. El acceso es el de la asistencia
(``SeccionDocenteMixin``): otra docente o un año CERRADO, 404 en GET y POST; otro rol y sin
sesión, ``RolRequeridoMixin``, con ``HX-Redirect`` cuando el guardado llega con ``HX-Request``.
"""

from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import dateformat, timezone
from django.views import View

from institucion.models import Periodo
from institucion.servicios import texto_seccion_corto
from institucion.views import SeccionDocenteMixin
from notas import servicios

SIN_PERIODOS = {
    "titulo": "La dirección aún no configura los periodos",
    "texto": "Cuando estén listos, podrás confirmar las competencias de tu sección.",
}
SIN_VIGENTE = "Hoy no hay un periodo vigente"


def _dia_y_mes_corto(fecha):
    """«9 mar.» (el idioma de la pantalla es LANGUAGE_CODE, es-pe)."""
    return f"{dateformat.format(fecha, 'j b')}."


def _dia_y_mes(fecha):
    """«9 de marzo»."""
    return dateformat.format(fecha, r"j \d\e F")


def _aviso(periodos):
    """El aviso de la pantalla cuando no hay un periodo vigente (spec «Sin periodo para marcar»)."""
    if not periodos:
        return SIN_PERIODOS
    if any(p.estado == servicios.VIGENTE for p in periodos):
        return None
    if any(p.editable for p in periodos):
        texto = (
            f"Elige uno de los {_palabra_periodo(periodos)}s ya pasados "
            "para revisar sus competencias."
        )
    else:
        primero = periodos[0]
        texto = f"El {primero.nombre_largo.lower()} empieza el {_dia_y_mes(primero.fecha_inicio)}."
    return {"titulo": SIN_VIGENTE, "texto": texto}


def _palabra_periodo(periodos):
    """«bimestre» o «trimestre»; «periodo» si el año no tiene periodos."""
    return periodos[0].nombre_largo.split()[0].lower() if periodos else "periodo"


def _nombres_elegibles(periodos):
    """Los periodos que se marcan, en lista de lectura: «B1», «B1 y B2», «B1, B2 y B3»."""
    nombres = [p.nombre for p in periodos if p.editable]
    if len(nombres) < 2:
        return "".join(nombres)
    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def _periodo_inicial(periodos, pedido):
    """El periodo de ``?periodo=N`` si se marca; si no, el vigente; si tampoco, ninguno (D8)."""
    for periodo in periodos:
        if str(periodo.numero) == pedido and periodo.editable:
            return periodo
    return next((p for p in periodos if p.estado == servicios.VIGENTE), None)


class CompetenciasView(SeccionDocenteMixin, View):
    """La pantalla de marcado; abrirla no guarda nada.

    Arma con D3, D4, D6 y D7 el contexto de la plantilla y, por periodo, el ``json_script`` que
    lee ``competencias.js``. Las notas y las obligatorias solo se calculan en los periodos que
    se marcan.
    """

    def get(self, request, seccion_id):
        seccion = self.seccion
        usuario = request.user
        areas = servicios.areas_de_la_seccion(usuario, seccion)
        permitido = servicios.universo_de_las_areas(areas)
        periodos = servicios.periodos_de_la_seccion(seccion, timezone.localdate())
        marcas = servicios.marcas_por_periodo(seccion, permitido)
        inicial = _periodo_inicial(periodos, request.GET.get("periodo", ""))
        por_periodo = []
        for periodo in periodos:
            con_notas, obligatorias = [], []
            if periodo.editable:
                con_notas = sorted(
                    c for c in permitido if servicios.tiene_notas(seccion, periodo.periodo, c)
                )
                obligatorias = sorted(
                    servicios.competencias_obligatorias(
                        usuario, seccion, periodo.periodo, permitido
                    )
                )
            por_periodo.append(
                {
                    "numero": periodo.numero,
                    "nombre": periodo.nombre,
                    "nombre_largo": periodo.nombre_largo,
                    "estado": periodo.estado,
                    "inicio": periodo.fecha_inicio.isoformat(),
                    "fin": periodo.fecha_fin.isoformat(),
                    "fechas": (
                        f"{_dia_y_mes_corto(periodo.fecha_inicio)} – "
                        f"{_dia_y_mes_corto(periodo.fecha_fin)}"
                    ),
                    "editable": periodo.editable,
                    "marcadas": marcas.get(periodo.periodo.pk),
                    "con_notas": con_notas,
                    "obligatorias": obligatorias,
                }
            )
        marcadas_iniciales, con_notas_iniciales, obligatorias_iniciales = set(), set(), set()
        if inicial is not None:
            dato = por_periodo[periodos.index(inicial)]
            marcadas_iniciales = servicios.estado_inicial(
                permitido, dato["marcadas"], dato["obligatorias"]
            )
            con_notas_iniciales = set(dato["con_notas"])
            obligatorias_iniciales = set(dato["obligatorias"])
        contexto = {
            "seccion": seccion,
            "seccion_corta": texto_seccion_corto(seccion),
            "areas": areas,
            "periodos": periodos,
            "periodo_inicial": inicial,
            "aviso": _aviso(periodos),
            "total": len(permitido),
            "marcadas_iniciales": marcadas_iniciales,
            "con_notas_iniciales": con_notas_iniciales,
            "obligatorias_iniciales": obligatorias_iniciales,
            "palabra_periodo": _palabra_periodo(periodos),
            "periodos_elegibles": _nombres_elegibles(periodos),
            "datos": {
                "inicial": inicial.numero if inicial else None,
                "total": len(permitido),
                # El JS lo devuelve al guardar: si el universo cambió, no se guarda (D5).
                "universo": sorted(permitido),
                # El JS cambia el 0 por el número del periodo que guarda.
                "url_guardar": reverse("competencias:guardar", args=[seccion.pk, 0]),
                "periodos": por_periodo,
            },
        }
        return render(request, "notas/competencias.html", contexto)


class GuardarView(SeccionDocenteMixin, View):
    """El conjunto completo del periodo (POST ``competencia`` repetido), todo o nada (D5).

    ``universo`` (repetido) es el universo que mostró la pantalla; si cambió, 400.

    204 guardado; 400 con ``mensaje`` (conjunto no válido o vacío); 404 periodo que no existe;
    409 con ``mensaje`` (periodo que no se marca) o con ``mensaje`` y ``competencias`` (con notas).
    """

    def post(self, request, seccion_id, numero):
        try:
            ids = [int(valor) for valor in request.POST.getlist("competencia")]
            visto = [int(valor) for valor in request.POST.getlist("universo")]
        except ValueError:
            return JsonResponse({"mensaje": servicios.CONJUNTO_NO_VALIDO}, status=400)
        try:
            servicios.guardar_marcas(request.user, self.seccion, numero, ids, visto=visto)
        except Periodo.DoesNotExist:
            return HttpResponse(status=404)
        except servicios.PeriodoNoMarcable as error:
            return JsonResponse({"mensaje": str(error)}, status=409)
        except servicios.CompetenciaConNotas as error:
            return JsonResponse(
                {"mensaje": str(error), "competencias": error.competencias}, status=409
            )
        except ValidationError as error:
            return JsonResponse({"mensaje": error.messages[0]}, status=400)
        return HttpResponse(status=204)
