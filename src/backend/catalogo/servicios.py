"""Reglas del catálogo curricular (design de EN-06, D4)."""

from catalogo.models import Area, InstitucionArea

# Aparece en el formato del SIAGIE, pero no se llena (decisión 5). La misma regla está copiada
# en la migración ``0002``, que la aplica a las instituciones que ya existían al migrar.
AREAS_QUE_NO_SE_TRABAJAN = {"0002"}


def asegurar_areas(institucion):
    """Crea las filas de ``institucion_area`` que le falten a ``institucion``.

    No toca las que ya existen: un «se trabaja» editado en el panel se respeta.
    """
    existentes = set(
        InstitucionArea.objects.filter(institucion=institucion).values_list("area_id", flat=True)
    )
    InstitucionArea.objects.bulk_create(
        [
            InstitucionArea(
                institucion=institucion,
                area=area,
                se_trabaja=area.codigo_siagie not in AREAS_QUE_NO_SE_TRABAJAN,
            )
            for area in Area.objects.exclude(pk__in=existentes)
        ],
        ignore_conflicts=True,
    )
