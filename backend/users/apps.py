from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения пользователей."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'

    def ready(self):
        """Подключение сигналов при старте."""
        pass
