from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from foodgram_backend.constants import LONG_TEXT, MEDIUM_TEXT
from users.managers import AccountManager
from users.validators import validate_name, validate_nickname


class UserAccount(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с авторизацией по email."""

    email = models.EmailField(
        _('email'),
        max_length=LONG_TEXT,
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким email уже существует'),
        },
    )
    username = models.CharField(
        _('логин'),
        max_length=MEDIUM_TEXT,
        unique=True,
        validators=[validate_nickname],
        error_messages={
            'unique': _('Пользователь с таким логином уже существует'),
        },
    )
    first_name = models.CharField(
        _('имя'),
        max_length=MEDIUM_TEXT,
        validators=[validate_name],
    )
    last_name = models.CharField(
        _('фамилия'),
        max_length=MEDIUM_TEXT,
        validators=[validate_name],
    )
    avatar = models.ImageField(
        _('аватар'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
    )

    # Статусные поля
    is_staff = models.BooleanField(
        _('статус персонала'),
        default=False,
        help_text=_('Доступ к админ-панели'),
    )
    is_active = models.BooleanField(
        _('активен'),
        default=True,
        help_text=_('Деактивируйте вместо удаления'),
    )
    date_joined = models.DateTimeField(
        _('дата регистрации'),
        default=timezone.now
    )

    objects = AccountManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
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
        verbose_name=_('подписчик'),
        help_text=_('Кто подписывается'),
    )
    target = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name=_('на кого подписан'),
        help_text=_('Цель подписки'),
    )
    created_at = models.DateTimeField(
        _('дата подписки'),
        auto_now_add=True,
    )

    class Meta:
        verbose_name = _('подписка')
        verbose_name_plural = _('подписки')
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

    def save(self, *args, **kwargs):
        """Предотвращение самоподписки."""
        if self.subscriber == self.target:
            raise ValueError(_('Нельзя подписаться на самого себя'))
        super().save(*args, **kwargs)
