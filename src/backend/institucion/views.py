"""Vistas de la lista de estudiantes de una sección (US-006, D4 y D5).

Cada vista arma su contenido una sola vez: con ``HX-Request`` responde el parcial para el
diálogo de la portada, más el aviso de la portada fuera de banda; sin ella, la página completa.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.views import View

from cuentas.acceso import RolRequeridoMixin, es_htmx
from cuentas.models import Usuario
from institucion import servicios
from institucion.forms import EstudianteForm, ListaPegadaForm
from institucion.models import Estudiante

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
            if "estudiante_id" in kwargs:
                # Un estudiante solo se alcanza a través de su propia sección (D4).
                self.estudiante = get_object_or_404(
                    self.seccion.estudiantes, pk=kwargs["estudiante_id"]
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


def _foco(formulario):
    """Apellidos, salvo que solo Nombres tenga error: el foco va al primer campo por corregir."""
    errores = formulario.errors
    return "nombres" if "nombres" in errores and "apellidos" not in errores else "apellidos"


class AgregarView(SeccionDocenteMixin, View):
    """Agregar (vista 6): "Guardar y agregar otro" vuelve aquí con 303 y "Estudiante agregado"."""

    def get(self, request, seccion_id):
        return self.responder(
            request, "_agregar", {"formulario": EstudianteForm(), "foco": "apellidos"}
        )

    def post(self, request, seccion_id):
        formulario = EstudianteForm(request.POST)
        if formulario.is_valid():
            try:
                servicios.agregar_estudiante(self.seccion, **formulario.cleaned_data)
            except ValidationError as error:
                formulario.add_error(None, error)
            else:
                messages.success(request, "Estudiante agregado", extra_tags=ETIQUETA_AVISO)
                return ver_otra(reverse("estudiantes:agregar", args=[self.seccion.pk]))
        return self.responder(
            request, "_agregar", {"formulario": formulario, "foco": _foco(formulario)}
        )


class EditarView(SeccionDocenteMixin, View):
    """Editar (vista 7): "Guardar cambios" vuelve a la lista con 303."""

    def get(self, request, seccion_id, estudiante_id):
        formulario = EstudianteForm(
            initial={"apellidos": self.estudiante.apellidos, "nombres": self.estudiante.nombres}
        )
        return self._responder(request, formulario)

    def post(self, request, seccion_id, estudiante_id):
        formulario = EstudianteForm(request.POST)
        if formulario.is_valid():
            try:
                servicios.editar_estudiante(self.estudiante, **formulario.cleaned_data)
            except Estudiante.DoesNotExist:
                raise Http404 from None
            except ValidationError as error:
                # El servicio deja en la instancia los valores rechazados: se vuelve a cargar.
                self.estudiante.refresh_from_db()
                formulario.add_error(None, error)
            else:
                return ver_otra(reverse("estudiantes:lista", args=[self.seccion.pk]))
        return self._responder(request, formulario)

    def _responder(self, request, formulario):
        contexto = {"formulario": formulario, "estudiante": self.estudiante}
        return self.responder(request, "_editar", {**contexto, "foco": _foco(formulario)})


class QuitarView(SeccionDocenteMixin, View):
    """Quitar (vista 8): confirmado, 303 a la lista. Con registros, el bloqueo y nada borrado."""

    def get(self, request, seccion_id, estudiante_id):
        return self.responder(request, "_quitar", {"estudiante": self.estudiante})

    def post(self, request, seccion_id, estudiante_id):
        try:
            servicios.quitar_estudiante(self.estudiante)
        except servicios.ListaConRegistros:
            contexto = {"estudiante": self.estudiante, "bloqueado": True}
            return self.responder(request, "_quitar", contexto)
        return ver_otra(reverse("estudiantes:lista", args=[self.seccion.pk]))


class VaciarView(SeccionDocenteMixin, View):
    """Vaciar (vista 9): confirmado, 303 a la lista vacía. Con registros, el bloqueo (9b) y
    ninguno borrado. Con la lista ya vacía no hay nada que confirmar: vuelve a la lista."""

    def get(self, request, seccion_id):
        if not self.seccion.estudiantes.exists():
            return ver_otra(reverse("estudiantes:lista", args=[self.seccion.pk]))
        return self.responder(request, "_vaciar")

    def post(self, request, seccion_id):
        try:
            servicios.vaciar_lista(self.seccion)
        except servicios.ListaConRegistros:
            return self.responder(request, "_vaciar", {"bloqueado": True})
        return ver_otra(reverse("estudiantes:lista", args=[self.seccion.pk]))
