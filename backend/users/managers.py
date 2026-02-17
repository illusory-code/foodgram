from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя."""

    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        """Создание пользователя с email и username."""
        if not email:
            raise ValueError(_('Email обязателен'))
        if not username:
            raise ValueError(_('Имя пользователя обязательно'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        """Создание обычного пользователя."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Создание суперпользователя."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_(
                'Суперпользователь должен иметь is_staff=True.'
            ))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_(
                'Суперпользователь должен иметь is_superuser=True.'
            ))

        return self._create_user(email, username, password, **extra_fields)
