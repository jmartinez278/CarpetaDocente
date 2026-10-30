"""Registro de actividad (documento 11, sección 3.7; design de US-008, D1, D3 y D8).

Cada entrada dice quién hizo qué y cuándo. El catálogo de operaciones es cerrado y la base lo
hace cumplir. Las entradas son de solo lectura: se crean con ``actividad.servicios.registrar``
y no se vuelven a guardar ni a borrar. ``QuerySet.update()`` y ``delete()`` no pasan por aquí;
el bloqueo en PostgreSQL es EN-04.
"""

from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Operacion(models.TextChoices):
    """Catálogo cerrado de operaciones. Cada historia que escribe datos agrega las suyas."""

    INICIO_SESION = "INICIO_SESION", "Inicio de sesión"
    CIERRE_SESION = "CIERRE_SESION", "Cierre de sesión"
    CUENTA_CREADA = "CUENTA_CREADA", "Cuenta creada"
    CUENTA_EDITADA = "CUENTA_EDITADA", "Cuenta editada"
    CUENTA_DESACTIVADA = "CUENTA_DESACTIVADA", "Cuenta desactivada"
    INSTITUCION_CREADA = "INSTITUCION_CREADA", "Institución creada"
    INSTITUCION_EDITADA = "INSTITUCION_EDITADA", "Institución editada"
    ANIO_CREADO = "ANIO_CREADO", "Año escolar creado"
    ANIO_EDITADO = "ANIO_EDITADO", "Año escolar editado"
    SECCION_CREADA = "SECCION_CREADA", "Sección creada"
    SECCION_EDITADA = "SECCION_EDITADA", "Sección editada"
    SECCION_ASIGNADA = "SECCION_ASIGNADA", "Sección asignada"
    SECCION_LIBERADA = "SECCION_LIBERADA", "Sección liberada"
    ESTUDIANTES_IMPORTADOS = "ESTUDIANTES_IMPORTADOS", "Estudiantes importados"
    ESTUDIANTE_AGREGADO = "ESTUDIANTE_AGREGADO", "Estudiante agregado"
    ESTUDIANTE_EDITADO = "ESTUDIANTE_EDITADO", "Estudiante editado"
    ESTUDIANTE_QUITADO = "ESTUDIANTE_QUITADO", "Estudiante quitado"
    LISTA_VACIADA = "LISTA_VACIADA", "Lista vaciada"
    REGISTRO_ASISTENCIA = "REGISTRO_ASISTENCIA", "Registro de asistencia"
    ASISTENCIA_CAMBIADA = "ASISTENCIA_CAMBIADA", "Asistencia cambiada"
    JORNADA_COMPLETA = "JORNADA_COMPLETA", "Jornada completa"
    CATALOGO_EDITADO = "CATALOGO_EDITADO", "Catálogo editado"
    DEMO_CARGADA = "DEMO_CARGADA", "Demostración cargada"
    DEMO_QUITADA = "DEMO_QUITADA", "Demostración quitada"
    SECCION_DESCARTADA = "SECCION_DESCARTADA", "Sección descartada"
    INTENTO_SIN_PERMISO = "INTENTO_SIN_PERMISO", "Intento sin permiso"
    REGISTRO_EXPORTADO = "REGISTRO_EXPORTADO", "Registro exportado"


# Operaciones que cuentan para KPI-01 (docentes activos). US-010 y US-020 agregan las suyas.
CUENTAN_KPI_01 = frozenset(
    {
        Operacion.REGISTRO_ASISTENCIA,
        Operacion.ASISTENCIA_CAMBIADA,
        Operacion.JORNADA_COMPLETA,
    }
)

# Operaciones del catálogo que aún no tienen quién las genere (la prueba de cobertura las salta).
RESERVADAS = frozenset({Operacion.INTENTO_SIN_PERMISO})


class RegistroActividad(models.Model):
    """Quién hizo qué y cuándo. Cadena vacía en vez de NULL, como en US-030.

    ``usuario`` queda vacío cuando lo hace un comando de consola o cuando se borra la cuenta.
    ``entidad`` es el ``db_table`` del modelo afectado y ``entidad_id`` su identificador como
    texto, para que la entrada sobreviva al borrado de lo que registra. El ``detalle`` solo lleva
    identificadores, códigos, cantidades y nombres de campos (RN-015).
    """

    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actividad",
        verbose_name="usuario",
    )
    # ``default`` y no ``auto_now_add``: las pruebas de semanas fijan la fecha.
    fecha_hora = models.DateTimeField("fecha y hora", default=timezone.now)
    operacion = models.CharField("operación", max_length=40, choices=Operacion)
    entidad = models.CharField("entidad", max_length=60, blank=True)
    entidad_id = models.CharField("identificador", max_length=40, blank=True)
    detalle = models.JSONField("detalle", default=dict, blank=True)

    class Meta:
        db_table = "registro_actividad"
        verbose_name = "entrada de actividad"
        verbose_name_plural = "registro de actividad"
        ordering = ["-fecha_hora", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(operacion__in=Operacion.values),
                name="ck_actividad_operacion",
            ),
        ]
        indexes = [
            models.Index(fields=["fecha_hora"], name="idx_actividad_fecha"),
            models.Index(fields=["usuario", "fecha_hora"], name="idx_actividad_usuario_fecha"),
            models.Index(fields=["operacion", "fecha_hora"], name="idx_actividad_operacion_fecha"),
        ]

    def __str__(self):
        return f"{self.fecha_hora:%d-%m-%Y %H:%M} – {self.operacion}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionDenied("El registro de actividad es de solo lectura.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("El registro de actividad es de solo lectura.")
