"""Mezcla ``RegistraEnPanel``: las escrituras del panel en el registro de actividad (US-008, D5).

Copia el ``LogEntry`` de Django: ``log_addition`` y ``log_change`` llaman a ``super()`` (el
historial del panel sigue igual) y luego a ``registrar`` con lo que devuelve
``operacion_del_panel``, que cada ``ModelAdmin`` define. Django llama a esos métodos dentro del
``atomic()`` de la ficha y del de la lista con ``list_editable``; donde no lo hace (el cambio de
contraseña), el ``ModelAdmin`` abre el suyo.

Los campos salen de ``construct_change_message`` (los nombres de ``form.changed_data``), nunca
de sus valores (RN-015).
"""

from actividad.servicios import registrar

AGREGAR = "agregar"
CAMBIAR = "cambiar"
# ``construct_change_message`` deja aquí los campos para el ``log_change`` que le sigue.
CAMPOS_DEL_PANEL = "_campos_del_panel"


class RegistraEnPanel:
    """Para los ``ModelAdmin`` que escriben. Ninguno permite borrar (RN-023)."""

    def operacion_del_panel(self, request, obj, accion, campos):
        """``[(operacion, detalle), ...]`` que deja ``accion`` sobre ``obj``.

        ``accion`` es ``AGREGAR`` o ``CAMBIAR``; ``campos``, los nombres de los campos que
        cambiaron. Una lista, porque un cambio puede dejar dos entradas (sección editada y
        asignada a la vez).
        """
        raise NotImplementedError

    def campos_cambiados(self, form):
        return list(form.changed_data)

    def construct_change_message(self, request, form, formsets, add=False):
        setattr(request, CAMPOS_DEL_PANEL, self.campos_cambiados(form))
        return super().construct_change_message(request, form, formsets, add)

    def log_addition(self, request, obj, message):
        entrada = super().log_addition(request, obj, message)
        self._registrar(request, obj, AGREGAR)
        return entrada

    def log_change(self, request, obj, message):
        entrada = super().log_change(request, obj, message)
        self._registrar(request, obj, CAMBIAR)
        return entrada

    def log_deletions(self, request, queryset):
        raise NotImplementedError(
            "Un ModelAdmin que registra en el panel no permite borrar: si se habilita, "
            "hay que registrar su operación (US-008, D5)."
        )

    def _registrar(self, request, obj, accion):
        campos = request.__dict__.pop(CAMPOS_DEL_PANEL, [])
        if accion == CAMBIAR and not campos:
            return  # guardar sin cambios no cambia datos
        for operacion, detalle in self.operacion_del_panel(request, obj, accion, campos):
            registrar(
                request.user,
                operacion,
                entidad=obj._meta.db_table,
                entidad_id=obj,
                detalle=detalle,
            )
