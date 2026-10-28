"""Vistas de la lista de estudiantes de una sección (US-006, D4 y D5).

Cada vista arma su contenido una sola vez: con ``HX-Request`` responde el parcial para el
diálogo de la portada, más el aviso de la portada fuera de banda; sin ella, la página completa.
"""

from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.views import View

from cuentas.acceso import RolRequeridoMixin, es_htmx
from cuentas.models import Usuario
from institucion import servicios
from institucion.forms import ListaPegadaForm

PLANTILLAS = "institucion/estudiantes/"
ETIQUETA_AVISO = "estudiantes"


def ver_otra(destino):
    """Post/Redirect/Get con 303 (D5): el XHR de HTMX la sigue con ``HX-Request``."""
    respuesta = HttpResponseRedirect(destino)
    respuesta.status_code = 303
    return respuesta


class SeccionDocenteMixin(RolRequeridoMixin):
    """Carga la sección de la docente: de otra docente o de un año CERRADO es un 404 (D4).

    La denegación con mensaje y registro es de US-004. Otro rol o sin sesión se resuelven
    antes, en ``RolRequeridoMixin``, sin consultar la sección.
    """

    rol_requerido = Usuario.Rol.DOCENTE

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol == self.rol_requerido:
            self.seccion = get_object_or_404(
                servicios.secciones_docente(request.user), pk=kwargs["seccion_id"]
            )
        return super().dispatch(request, *args, **kwargs)

    def responder(self, request, parcial, contexto=None, status=200):
        """El parcial en el diálogo (con el aviso de la portada) o la página completa (D5)."""
        cantidad = self.seccion.estudiantes.count()
        contexto = {
            "seccion": self.seccion,
            "titulo": f"Estudiantes de {servicios.texto_seccion_corto(self.seccion)}",
            "cantidad": cantidad,
            "parcial": f"{PLANTILLAS}{parcial}.html",
            "en_dialogo": es_htmx(request),
            **(contexto or {}),
        }
        plantilla = "dialogo" if es_htmx(request) else "pagina"
        return render(request, f"{PLANTILLAS}{plantilla}.html", contexto, status=status)


class ListaView(SeccionDocenteMixin, View):
    """La lista de la sección, o la vista de lista vacía (D4: vistas 2 y 5 del boceto)."""

    def get(self, request, seccion_id):
        estudiantes = servicios.estudiantes_ordenados(self.seccion)
        parcial = "_lista" if estudiantes else "_lista_vacia"
        return self.responder(request, parcial, {"estudiantes": estudiantes})


class PegarView(SeccionDocenteMixin, View):
    """Pegar lista y Revisar lista (vistas 3 y 4), solo con la sección vacía (D2, D5).

    Correcto: 303 a la lista con el aviso de éxito (una sola vez). Con errores: 200 con el
    texto intacto y cada error. Con estudiantes: el aviso, sin el cuadro, y nada guardado.
    """

    def get(self, request, seccion_id):
        if self.seccion.estudiantes.exists():
            return self.responder(request, "_pegar_con_estudiantes")
        return self.responder(request, "_pegar", {"texto": ""})

    def post(self, request, seccion_id):
        formulario = ListaPegadaForm(request.POST)
        formulario.is_valid()
        texto = formulario.cleaned_data.get("lista", "")
        try:
            cantidad, errores = servicios.importar_lista(self.seccion, texto)
        except servicios.SeccionConEstudiantes:
            return self.responder(request, "_pegar_con_estudiantes")
        if errores:
            return self.responder(request, "_pegar", {"texto": texto, "errores": errores})
        importados = f"{cantidad} estudiante{pluralize(cantidad)} importado{pluralize(cantidad)}"
        messages.success(
            request,
            f"{importados}\n\nRevisa los nombres; puedes corregirlos con Editar",
            extra_tags=ETIQUETA_AVISO,
        )
        return ver_otra(reverse("estudiantes:lista", args=[self.seccion.pk]))


class PendienteView(SeccionDocenteMixin, View):
    """Marcador de las rutas que el resto de la historia completa (grupo 2, partes B y C)."""

    def get(self, request, *args, **kwargs):
        raise Http404
