from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalogo"

    def ready(self):
        from catalogo import signals  # noqa: F401  (conecta el receptor de post_save de Institucion)
