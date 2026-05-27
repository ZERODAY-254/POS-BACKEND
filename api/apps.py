from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'System Configuration'

    def ready(self):
        from . import excel_sync  # noqa: F401
