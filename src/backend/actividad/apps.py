from django.apps import AppConfig


class ActividadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "actividad"

    def ready(self):
        # Señales de inicio y cierre de sesión (D4).
        from actividad import signals  # noqa: F401
