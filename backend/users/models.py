from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from foodgram_backend.constants import TEXT_LENGTH_MAX, TEXT_LENGTH_MEDIUM
from users.managers import UserManager
from users.validators import validate_full_name, validate_username_format


class UserAccount(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с email в качестве логина."""

    email = models.EmailField(
        _('email address'),
        max_length=TEXT_LENGTH_MAX,
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким email уже существует.'),
        },
    )
    username = models.CharField(
        _('username'),
        max_length=TEXT_LENGTH_MEDIUM,
        unique=True,
        validators=[validate_username_format],
        error_messages={
            'unique': _('Пользователь с таким именем уже существует.'),
        },
    )
    first_name = models.CharField(
        _('first name'),
        max_length=TEXT_LENGTH_MEDIUM,
        validators=[validate_full_name],
    )
    last_name = models.CharField(
        _('last name'),
        max_length=TEXT_LENGTH_MEDIUM,
        validators=[validate_full_name],
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
    )

    # Status fields
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Может ли пользователь входить в админ-панель.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Отключите вместо удаления аккаунта.'
        ),
    )
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """Возвращает полное имя."""
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
    def recipe_count(self):
        """Количество рецептов пользователя."""
        return self.own_recipes.count()

    @property
    def followers_count(self):
        """Количество подписчиков."""
        return self.followers.count()

    @property
    def following_count(self):
        """Количество подписок."""
        return self.following.count()


class FollowRelationship(models.Model):
    """Модель подписки одного пользователя на другого."""

    follower = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('подписчик'),
        help_text=_('Кто подписывается'),
    )
    following = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name=_('на кого подписан'),
        help_text=_('На кого оформлена подписка'),
    )
    created_at = models.DateTimeField(
        _('subscription date'),
        auto_now_add=True,
    )

    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follow_relationship'
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F('following')),
                name='prevent_self_follow'
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.follower.username} → {self.following.username}'

    def save(self, *args, **kwargs):
        """Проверка на самоподписку перед сохранением."""
        if self.follower == self.following:
            raise ValueError(_('Нельзя подписаться на самого себя'))
        super().save(*args, **kwargs)
