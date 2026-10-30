from django.apps import AppConfig


class ActividadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "actividad"

    def ready(self):
        from actividad import signals  # noqa: F401  (inicio y cierre de sesión, D4)
