"""Глобальные константы проекта."""

# Ограничения для ингредиентов в рецепте
INGREDIENT_AMOUNT_MIN = 1
INGREDIENT_AMOUNT_MAX = 10000  # 10 кг максимум

# Временные рамки приготовления (в минутах)
COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 32000
# Параметры изображений
IMAGE_SIZE_LIMIT = 33  # Мб или другие единицы

# Пагинация
PAGINATION_DEFAULT = 6
PAGINATION_MAX = 100

# Ограничения длины текстовых полей
TEXT_LENGTH_SHORT = 50
TEXT_LENGTH_MEDIUM = 150
TEXT_LENGTH_LONG = 254
