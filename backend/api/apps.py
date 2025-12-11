
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    # Esto cambia el título en el admin de "API" a algo legible
    verbose_name = "Gestión Municipal de Aguas"