import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from foodgram_backend.constants import TEXT_LENGTH_MEDIUM


def validate_full_name(value):
    """Валидация имени и фамилии."""
    if not value:
        raise ValidationError(_('Поле обязательно для заполнения.'))
    if len(value) > TEXT_LENGTH_MEDIUM:
        raise ValidationError(
            _('Максимальная длина — %(max)d символов.'),
            params={'max': TEXT_LENGTH_MEDIUM},
        )
    # Проверка на недопустимые символы
    if not re.match(r'^[А-Яа-яЁёA-Za-z\- ]+$', value):
        raise ValidationError(
            _('Используйте только буквы, дефисы и пробелы.')
        )
    # Проверка на минимум 2 символа
    if len(value.strip()) < 2:
        raise ValidationError(_('Минимум 2 символа.'))


def validate_username_format(value):
    """Валидация имени пользователя."""
    if value.lower() == 'me':
        raise ValidationError(_('Имя "me" запрещено.'))
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            _('Используйте только буквы, цифры и символы @/./+/-/_.')
        )
    if len(value) > TEXT_LENGTH_MEDIUM:
        raise ValidationError(
            _('Максимальная длина — %(max)d символов.'),
            params={'max': TEXT_LENGTH_MEDIUM},
        )


# Для обратной совместимости с импортами
username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message=_('Введите корректное имя пользователя.'),
    flags=re.UNICODE,
)
