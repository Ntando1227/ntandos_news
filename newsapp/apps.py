"""Configure the news application."""
from django.apps import AppConfig


class NewsappConfig(AppConfig):
    """Configure the newsapp application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'newsapp'

    def ready(self):
        """Load application signal handlers."""
        import newsapp.signals
