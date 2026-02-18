import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from foodgram_backend.constants import MEDIUM_TEXT


def validate_name(value):
    """Валидация имени и фамилии."""
    if not value:
        raise ValidationError(_('Обязательное поле'))
    if len(value) > MEDIUM_TEXT:
        raise ValidationError(
            _('Максимум %(max)d символов'),
            params={'max': MEDIUM_TEXT},
        )
    if not re.match(r'^[А-Яа-яЁёA-Za-z\- ]+$', value):
        raise ValidationError(_('Только буквы, дефисы и пробелы'))
    if len(value.strip()) < 2:
        raise ValidationError(_('Минимум 2 символа'))


def validate_nickname(value):
    """Валидация логина пользователя."""
    if value.lower() == 'me':
        raise ValidationError(_('Логин "me" запрещён'))
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            _('Только буквы, цифры и символы @/./+/-/_.')
        )
    if len(value) > MEDIUM_TEXT:
        raise ValidationError(
            _('Максимум %(max)d символов'),
            params={'max': MEDIUM_TEXT},
        )


# Для обратной совместимости
username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message=_('Введите корректный логин'),
    flags=re.UNICODE,
)
