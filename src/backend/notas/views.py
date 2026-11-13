"""Vistas de las competencias de una sección (design de US-029, D8).

Solo leen la petición y llaman a ``notas.servicios``. El acceso es el de la asistencia
(``SeccionDocenteMixin``): sección ajena, inexistente o de un año CERRADO, 403 con registro en
GET y POST (US-004); otro rol y sin
sesión, ``RolRequeridoMixin``, con ``HX-Redirect`` cuando el guardado llega con ``HX-Request``.
"""

import json

from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import dateformat, timezone
from django.utils.http import urlencode
from django.views import View

from catalogo.models import InstitucionArea
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


def _aviso(periodos, romanos=False):
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
        nombre = primero.nombre_romano if romanos else primero.nombre_largo.lower()
        texto = f"El {nombre} empieza el {_dia_y_mes(primero.fecha_inicio)}."
    return {"titulo": SIN_VIGENTE, "texto": texto}


def _palabra_periodo(periodos):
    """«bimestre» o «trimestre»; «periodo» si el año no tiene periodos."""
    return periodos[0].nombre_largo.split()[0].lower() if periodos else "periodo"


def _nombres_elegibles(periodos):
    """Los periodos que se marcan, en lista de lectura: «I», «I y II», «I, II y III»."""
    nombres = [p.romano for p in periodos if p.editable]
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
                    permitido & servicios.competencias_con_notas(seccion, periodo.periodo)
                )
                obligatorias = sorted(
                    servicios.competencias_obligatorias(
                        usuario, seccion, periodo.periodo, permitido
                    )
                )
            por_periodo.append(
                {
                    "numero": periodo.numero,
                    "nombre": periodo.nombre_romano,
                    "corto": periodo.romano,
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
        codigos = [a.area.codigo_siagie for a in areas]
        pedida = request.GET.get("area", "")
        area_inicial = pedida if pedida in codigos else (codigos[0] if codigos else "")
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
            "aviso": _aviso(periodos, romanos=True),
            "total": len(permitido),
            "marcadas_iniciales": marcadas_iniciales,
            "con_notas_iniciales": con_notas_iniciales,
            "obligatorias_iniciales": obligatorias_iniciales,
            "palabra_periodo": _palabra_periodo(periodos),
            "periodos_elegibles": _nombres_elegibles(periodos),
            "area_inicial": area_inicial,
            # El enlace «Registrar notas de B*n*»: competencias.js lo cambia al pasar de periodo.
            "url_notas": reverse("notas:hoja", args=[seccion.pk]),
            "sin_marcas_de": (
                inicial if inicial is not None and request.GET.get("desde") == "notas" else None
            ),
            "datos": {
                "inicial": inicial.numero if inicial else None,
                "area_inicial": area_inicial,
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
        except servicios.PeriodoNoMarcable:
            return JsonResponse({"mensaje": servicios.PERIODO_NO_MARCABLE}, status=409)
        except servicios.CompetenciaConNotas as error:
            return JsonResponse(
                {"mensaje": servicios.MENSAJE_CON_NOTAS, "competencias": error.competencias},
                status=409,
            )
        except ValidationError as error:
            return JsonResponse({"mensaje": error.messages[0]}, status=400)
        return HttpResponse(status=204)


# --- Hoja de notas (design de US-020, D3, D8, D9) ---


# Prefijo de la clave del borrador de un área (D10); notas.js le suma el código SIAGIE del área.
CLAVE_BORRADOR = "cd:notas:v1:u{usuario}:s{seccion}:p{numero}:a"


def _nombre(estudiante):
    return f"{estudiante.apellidos}, {estudiante.nombres}"


def _area_inicial(hojas, pedida):
    """El área de ``?area=`` si la institución la trabaja; si no, la primera con columnas (D3)."""
    if any(hoja.area.codigo_siagie == pedida for hoja in hojas):
        return pedida
    return next((hoja.area.codigo_siagie for hoja in hojas if hoja.columnas), None)


def _ir_a_competencias(seccion, periodo, hojas, pedida):
    """302 a Competencias del periodo, con el área y ``desde=notas`` (D3; spec «Bimestre sin
    marcas»). El área es la pedida si la institución la trabaja; si no, la primera que se marca."""
    if not any(hoja.area.codigo_siagie == pedida for hoja in hojas):
        pedida = next((hoja.area.codigo_siagie for hoja in hojas if hoja.marcable), "")
    consulta = {"periodo": periodo.numero, "area": pedida, "desde": "notas"}
    if not pedida:
        del consulta["area"]
    return redirect(f"{reverse('competencias:pantalla', args=[seccion.pk])}?{urlencode(consulta)}")


def _datos_del_area(hoja, seccion, periodo):
    """Lo que ``notas.js`` necesita para dibujar y guardar la hoja de un área (D2, D4, D9)."""
    codigo = hoja.area.codigo_siagie
    return {
        "codigo": codigo,
        "nombre": hoja.area.nombre,
        "a_cargo": hoja.a_cargo,
        "marcable": hoja.marcable,
        "total": hoja.total,
        "columnas": [
            {
                "id": columna.competencia.pk,
                "etiqueta": columna.etiqueta,
                "nombre": columna.competencia.nombre,
            }
            for columna in hoja.columnas
        ],
        "filas": [{"id": e.pk, "nombre": _nombre(e)} for e in hoja.filas],
        "solo_lectura": [
            {"id": e.pk, "nombre": _nombre(e), "estado": e.estado} for e in hoja.solo_lectura
        ],
        "notas": {
            f"{estudiante}-{competencia}": {"nivel": nivel, "conclusion": conclusion}
            for (estudiante, competencia), (nivel, conclusion) in hoja.notas.items()
        },
        "faltantes": hoja.faltantes,
        "url_guardar": reverse("notas:guardar", args=[seccion.pk, periodo.numero, codigo]),
    }


class HojaView(SeccionDocenteMixin, View):
    """La hoja de notas de la sección en el periodo de D3; abrirla no guarda nada.

    Sin periodo que abrir (sin periodos o antes del primero), solo el aviso. Sin competencias
    guardadas del periodo, lleva a Competencias. Si no, el marco de la plantilla y, en
    ``json_script``, las áreas con sus columnas, filas, notas y faltantes.
    """

    def get(self, request, seccion_id):
        seccion, usuario = self.seccion, request.user
        periodos = servicios.periodos_de_la_seccion(seccion, timezone.localdate())
        periodo = servicios.periodo_de_la_hoja(periodos, request.GET.get("periodo", ""))
        contexto = {
            "seccion": seccion,
            "seccion_corta": texto_seccion_corto(seccion),
            "periodo": periodo,
            # Todos los del año, también el futuro: el selector los pinta (rebrand-us-020, D1).
            "periodos": periodos,
            "aviso": _aviso(periodos, romanos=True),
            "palabra_periodo": _palabra_periodo(periodos),
        }
        if periodo is None:
            return render(request, "notas/hoja.html", contexto)
        areas = servicios.areas_de_la_seccion(usuario, seccion)
        hojas = servicios.hoja_de_notas(usuario, seccion, periodo.periodo, areas)
        pedida = request.GET.get("area", "")
        if not any(hoja.columnas for hoja in hojas):
            return _ir_a_competencias(seccion, periodo, hojas, pedida)
        inicial = _area_inicial(hojas, pedida)
        consulta = urlencode({"periodo": periodo.numero, "area": inicial})
        contexto.update(
            {
                "hojas": hojas,
                "area_inicial": inicial,
                # Los enlaces del selector de periodo (rebrand-us-020, D1).
                "url_hoja": reverse("notas:hoja", args=[seccion.pk]),
                "url_competencias": (
                    f"{reverse('competencias:pantalla', args=[seccion.pk])}?{consulta}"
                ),
                "datos": {
                    "periodo": {
                        "numero": periodo.numero,
                        "nombre": periodo.nombre_romano,
                        "estado": periodo.estado,
                    },
                    "area_inicial": inicial,
                    "clave_borrador": CLAVE_BORRADOR.format(
                        usuario=usuario.pk, seccion=seccion.pk, numero=periodo.numero
                    ),
                    # Para nombrar en el diálogo de salida los borradores de otros periodos (D11).
                    "periodos": [
                        {"numero": p.numero, "nombre": p.nombre_romano}
                        for p in periodos
                        if p.editable
                    ],
                    "areas": [_datos_del_area(hoja, seccion, periodo) for hoja in hojas],
                },
            }
        )
        return render(request, "notas/hoja.html", contexto)


def _leer_cuerpo(request):
    """Las celdas del cuerpo JSON, o ``HojaCambiada`` si no es un objeto con ``celdas``."""
    try:
        cuerpo = json.loads(request.body)
    except ValueError as error:  # JSON mal formado o bytes que no son UTF-8
        raise servicios.HojaCambiada from error
    if not isinstance(cuerpo, dict) or "celdas" not in cuerpo:
        raise servicios.HojaCambiada
    return cuerpo["celdas"]


class GuardarHojaView(SeccionDocenteMixin, View):
    """Las celdas de la hoja de un área en un periodo, en un cuerpo JSON, todo o nada (D5, D8).

    200 ``faltantes``; 400 ``mensaje`` con ``no_validas`` y ``sin_conclusion`` (escala o
    conclusión) o solo ``mensaje`` (estructura o JSON mal formado); 404 periodo o área que no
    existen; 409 ``mensaje`` (periodo no editable) o ``mensaje`` y ``cambiadas`` (D7). Los mensajes
    son constantes del servicio, nunca el texto de la excepción.
    """

    def post(self, request, seccion_id, numero, area):
        try:
            celdas = _leer_cuerpo(request)
            resultado = servicios.guardar_hoja(request.user, self.seccion, numero, area, celdas)
        except (Periodo.DoesNotExist, InstitucionArea.DoesNotExist):
            return HttpResponse(status=404)
        except servicios.HojaCambiada:
            return JsonResponse({"mensaje": servicios.HOJA_CAMBIADA}, status=400)
        except servicios.HojaConErrores as error:
            mensaje = servicios.VALOR_NO_VALIDO if error.no_validas else servicios.FALTA_CONCLUSION
            return JsonResponse(
                {
                    "mensaje": mensaje,
                    "no_validas": [list(par) for par in error.no_validas],
                    "sin_conclusion": [list(par) for par in error.sin_conclusion],
                },
                status=400,
            )
        except servicios.PeriodoNoEditable:
            return JsonResponse({"mensaje": servicios.PERIODO_NO_EDITABLE}, status=409)
        except servicios.NotasCambiadas as error:
            return JsonResponse(
                {"mensaje": servicios.NOTAS_CAMBIADAS, "cambiadas": error.cambiadas}, status=409
            )
        return JsonResponse({"faltantes": resultado.faltantes})
