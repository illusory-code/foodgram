from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения управления пользователями."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Управление пользователями'

    def ready(self):
        """Подключение обработчиков сигналов."""
        pass
