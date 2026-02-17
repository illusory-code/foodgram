from django.apps import AppConfig


class RecipeApplicationConfig(AppConfig):
    """Конфигурация приложения рецептов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'Кулинарные рецепты'

    def ready(self):
        """Инициализация приложения."""
        pass
