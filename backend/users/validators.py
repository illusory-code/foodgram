import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from foodgram_backend.constants import MAX_NAME_LENGTH


def validate_name(value):
    """Валидация имени и фамилии."""
    if not value:
        raise ValidationError('Обязательное поле')
    if len(value) > MAX_NAME_LENGTH:
        raise ValidationError(
            'Максимум %(max)d символов',
            params={'max': MAX_NAME_LENGTH},
        )
    if not re.match(r'^[А-Яа-яЁёA-Za-z\- ]+$', value):
        raise ValidationError('Только буквы, дефисы и пробелы')
    if len(value.strip()) < 2:
        raise ValidationError('Минимум 2 символа')


def validate_nickname(value):
    """Валидация логина пользователя."""
    if value.lower() == 'me':
        raise ValidationError('Логин "me" запрещён')
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Только буквы, цифры и символы @/./+/-/_.'
        )
    if len(value) > MAX_NAME_LENGTH:
        raise ValidationError(
            'Максимум %(max)d символов',
            params={'max': MAX_NAME_LENGTH},
        )


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Введите корректный логин',
    flags=re.UNICODE,
)
