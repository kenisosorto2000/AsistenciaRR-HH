from django.apps import AppConfig


class MarcajeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marcaje'

    def ready(self):
        import marcaje.signals  # <--- Aquí estamos cargando el archivo signals.py