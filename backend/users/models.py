from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from foodgram_backend.constants import LONG_TEXT, MAX_NAME_LENGTH
from users.managers import AccountManager
from users.validators import validate_name, validate_nickname


class UserAccount(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с авторизацией по email."""

    email = models.EmailField(
        'email',
        max_length=LONG_TEXT,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует',
        },
    )
    username = models.CharField(
        'логин',
        max_length=MAX_NAME_LENGTH,
        unique=True,
        validators=[validate_nickname],
        error_messages={
            'unique': 'Пользователь с таким логином уже существует',
        },
    )
    first_name = models.CharField(
        'имя',
        max_length=MAX_NAME_LENGTH,
        validators=[validate_name],
    )
    last_name = models.CharField(
        'фамилия',
        max_length=MAX_NAME_LENGTH,
        validators=[validate_name],
    )
    avatar = models.ImageField(
        'аватар',
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        default='',
    )

    is_staff = models.BooleanField(
        'статус персонала',
        default=False,
        help_text='Доступ к админ-панели',
    )
    is_active = models.BooleanField(
        'активен',
        default=True,
        help_text='Деактивируйте вместо удаления',
    )
    date_joined = models.DateTimeField(
        'дата регистрации',
        default=timezone.now
    )

    objects = AccountManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """Возвращает полное имя пользователя."""
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        """Возвращает короткое имя (email)."""
        return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Отправляет email пользователю."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return f'{self.username} ({self.email})'

    @property
    def recipes_created(self):
        """Количество созданных рецептов."""
        return self.created_recipes.count()

    @property
    def subscribers_count(self):
        """Количество подписчиков."""
        return self.followers.count()

    @property
    def subscriptions_count(self):
        """Количество подписок."""
        return self.following.count()


class FollowRelationship(models.Model):
    """Модель подписки пользователя на другого пользователя."""

    subscriber = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='подписчик',
        help_text='Кто подписывается',
    )
    target = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='на кого подписан',
        help_text='Цель подписки',
    )
    created_at = models.DateTimeField(
        'дата подписки',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'target'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('target')),
                name='no_self_follow'
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subscriber.username} → {self.target.username}'
