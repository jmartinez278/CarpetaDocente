from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cuentas"

    def ready(self):
        from cuentas import middleware  # noqa: F401  (conecta el receptor de user_logged_in)
