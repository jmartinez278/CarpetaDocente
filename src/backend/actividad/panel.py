"""Mezcla ``RegistraEnPanel``: las escrituras del panel en el registro de actividad (US-008, D5).

Copia el ``LogEntry`` de Django: ``log_addition`` y ``log_change`` llaman a ``super()`` (el
historial del panel sigue igual) y luego a ``registrar`` con lo que devuelve
``operacion_del_panel``, que cada ``ModelAdmin`` define. Django llama a esos métodos dentro del
``atomic()`` de la ficha y del de la lista con ``list_editable``; donde no lo hace (el cambio de
contraseña), el ``ModelAdmin`` abre el suyo.

Los campos salen de ``construct_change_message`` (los nombres de ``form.changed_data``), nunca
de sus valores (RN-015). ``changed_data`` compara con la fila leída al recibir el POST: la mezcla
la lee con ``FOR UPDATE`` para que nadie la cambie entre esa lectura y el guardado. Si no, un
guardado podría revertir un cambio ajeno sin que conste (RNF-016).
"""

from django.db import connection, router, transaction

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

    def get_object(self, request, object_id, from_field=None):
        """En un POST, la ficha y el cambio de contraseña usan la fila releída y bloqueada."""
        obj = super().get_object(request, object_id, from_field)
        if obj is None or request.method != "POST" or not connection.in_atomic_block:
            return obj
        return self.get_queryset(request).select_for_update(of=("self",)).filter(pk=obj.pk).first()

    def changelist_view(self, request, extra_context=None):
        """Django lee las filas de ``list_editable`` fuera de su ``atomic()``: aquí van dentro."""
        if request.method != "POST":
            return super().changelist_view(request, extra_context)
        with transaction.atomic(using=router.db_for_write(self.model)):
            return super().changelist_view(request, extra_context)

    def _get_list_editable_queryset(self, request, prefix):
        return super()._get_list_editable_queryset(request, prefix).select_for_update(of=("self",))

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
