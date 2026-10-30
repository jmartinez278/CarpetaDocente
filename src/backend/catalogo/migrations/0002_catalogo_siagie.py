"""Carga el catálogo del registro de notas del SIAGIE (design de EN-06, D2 a D4).

Los textos están copiados aquí, no importados: una migración da siempre el mismo resultado
aunque el código cambie después. Un cambio del catálogo es una migración nueva.

Áreas: hoja Generalidades, con mayúsculas normales; ``orden`` es su posición (1 a 11).
Competencias: LEYENDA de cada hoja, con su orden 01…n; la única corrección es «aprendizaje»
en minúscula en 0007 (D2).

``get_or_create`` por código (área), por (área, nombre) (competencia) y por (institución,
área): repetir la carga no duplica ni pisa lo editado en el panel. La reversa no borra:
deshacer ``0001`` borra las tablas, y borrar el catálogo a mano chocaría con RN-023.
"""

from django.db import migrations

# (código SIAGIE, nombre, es_transversal, admite_exoneracion, competencias en orden 01…n)
CATALOGO = [
    (
        "0001",
        "Arte y Cultura",
        False,
        False,
        [
            "Aprecia de manera crítica manifestaciones artístico-culturales",
            "Crea proyectos desde los lenguajes artísticos",
        ],
    ),
    (
        "0002",
        "Castellano como segunda lengua",
        False,
        False,
        [
            "Se comunica oralmente",
            "Lee diversos tipos de textos escritos",
            "Escribe diversos tipos de textos",
        ],
    ),
    (
        "0003",
        "Inglés como lengua extranjera",
        False,
        False,
        [
            "Se comunica oralmente en inglés como lengua extranjera",
            "Lee diversos tipos de textos escritos en inglés como lengua extranjera",
            "Escribe diversos tipos de textos en inglés como lengua extranjera",
        ],
    ),
    (
        "0004",
        "Ciencia y Tecnología",
        False,
        False,
        [
            "Indaga mediante métodos científicos para construir sus conocimientos",
            "Explica el mundo físico basándose en conocimientos sobre los seres vivos; materia"
            " y energía; biodiversidad, Tierra y Universo",
            "Diseña y construye soluciones tecnológicas para resolver problemas de su entorno",
        ],
    ),
    (
        "0005",
        "Comunicación",
        False,
        False,
        [
            "Se comunica oralmente en su lengua materna",
            "Lee diversos tipos de textos escritos en su lengua materna",
            "Escribe diversos tipos de textos en su lengua materna",
        ],
    ),
    (
        "031",
        "Educación Física",
        False,
        True,
        [
            "Se desenvuelve de manera autónoma a través de su motricidad",
            "Asume una vida saludable",
            "Interactúa a través de sus habilidades sociomotrices",
        ],
    ),
    (
        "035",
        "Educación Religiosa",
        False,
        True,
        [
            "Construye su identidad como persona humana, amada por Dios, digna, libre y"
            " trascendente, comprendiendo la doctrina de su propia religión, abierto al diálogo"
            " con las que le son cercanas",
            "Asume la experiencia del encuentro personal y comunitario con Dios en su proyecto"
            " de vida en coherencia con su creencia religiosa",
        ],
    ),
    (
        "063",
        "Matemática",
        False,
        False,
        [
            "Resuelve problemas de cantidad",
            "Resuelve problemas de regularidad, equivalencia y cambio",
            "Resuelve problemas de forma, movimiento y localización",
            "Resuelve problemas de gestión de datos e incertidumbre",
        ],
    ),
    (
        "067",
        "Personal Social",
        False,
        False,
        [
            "Construye su identidad",
            "Convive y participa democráticamente en la búsqueda del bien común",
            "Construye interpretaciones históricas",
            "Gestiona responsablemente el espacio y el ambiente",
            "Gestiona responsablemente los recursos económicos",
        ],
    ),
    (
        "0006",
        "Se desenvuelve en entornos virtuales generados por las TIC",
        True,
        False,
        ["Se desenvuelve en entornos virtuales generados por las TIC"],
    ),
    (
        "0007",
        "Gestiona su aprendizaje de manera autónoma",
        True,
        False,
        ["Gestiona su aprendizaje de manera autónoma"],
    ),
]

# Aparece en el formato del SIAGIE, pero no se llena (decisión 5; D4).
AREAS_QUE_NO_SE_TRABAJAN = {"0002"}


def cargar_catalogo(apps, schema_editor):
    """Crea lo que falte del catálogo y las áreas de cada institución, sin tocar lo existente.

    La fixture ``catalogo`` de ``conftest.py`` la llama con ``django.apps.apps``.
    """
    Area = apps.get_model("catalogo", "Area")
    Competencia = apps.get_model("catalogo", "Competencia")
    InstitucionArea = apps.get_model("catalogo", "InstitucionArea")
    Institucion = apps.get_model("institucion", "Institucion")

    areas = []
    for orden, (codigo, nombre, transversal, exoneracion, competencias) in enumerate(
        CATALOGO, start=1
    ):
        area, _ = Area.objects.get_or_create(
            codigo_siagie=codigo,
            defaults={
                "nombre": nombre,
                "es_transversal": transversal,
                "admite_exoneracion": exoneracion,
                "orden": orden,
            },
        )
        areas.append(area)
        for orden_competencia, competencia in enumerate(competencias, start=1):
            Competencia.objects.get_or_create(
                area=area, nombre=competencia, defaults={"orden": orden_competencia}
            )

    for institucion in Institucion.objects.all():
        for area in areas:
            InstitucionArea.objects.get_or_create(
                institucion=institucion,
                area=area,
                defaults={"se_trabaja": area.codigo_siagie not in AREAS_QUE_NO_SE_TRABAJAN},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_catalogo, migrations.RunPython.noop),
    ]
