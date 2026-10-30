"""Receptores de señales del catálogo; se conectan en ``CatalogoConfig.ready()`` (D4).

Una señal y no una llamada desde ``institucion``: ``catalogo`` depende de ``institucion`` y no
al revés, y así toda vía de alta (panel, shell, pruebas) recibe sus áreas.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from catalogo import servicios
from institucion.models import Institucion


@receiver(post_save, sender=Institucion, dispatch_uid="catalogo_areas_de_institucion_nueva")
def areas_de_institucion_nueva(sender, instance, created, raw, **kwargs):
    """Da a una institución recién creada sus 11 áreas; al cargar una fixture no hace nada."""
    if created and not raw:
        servicios.asegurar_areas(instance)
