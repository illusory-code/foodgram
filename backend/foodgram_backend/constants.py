# Лимиты для ингредиентов в рецепте
INGREDIENT_QTY_MIN = 1
INGREDIENT_QTY_MAX = 10000  # максимум 10 кг

# Время приготовления (минуты)
COOKING_DURATION_MIN = 1
COOKING_DURATION_MAX = 32000

# Ограничения изображений
MAX_IMAGE_SIZE_MB = 33

# Настройки пагинации
DEFAULT_PAGE_SIZE = 6
MAX_PAGE_SIZE = 100

# Длины текстовых полей
SHORT_TEXT = 50
MAX_NAME_LENGTH = 150
LONG_TEXT = 254
USERNAME_MAX_LEN = 150

# Для сериализаторов рецептов
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000

# Константы для моделей приложения recipes
TAG_NAME_MAX_LENGTH = 100
TAG_SLUG_MAX_LENGTH = 100
TAG_COLOR_MAX_LENGTH = 7
INGREDIENT_UNIT_MAX_LENGTH = 50
