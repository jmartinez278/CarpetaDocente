from django.db import migrations, models


class Migration(migrations.Migration):
    """``grado_hasta`` admite nulo durante el despliegue (US-018, revisión A2).

    ``migrate`` corre antes de publicar el código nuevo: el código anterior inserta sesiones sin
    ``grado_hasta`` y, con NOT NULL, fallaría. Los CHECK dejan pasar el nulo y se lee como
    ``grado``. Volver a NOT NULL, con las filas ya rellenas, es una migración posterior.
    """

    dependencies = [("repositorio", "0003_sesion_referencia")]

    operations = [
        migrations.AlterField(
            model_name="sesion",
            name="grado_hasta",
            field=models.SmallIntegerField(blank=True, null=True, verbose_name="grado final"),
        ),
    ]
