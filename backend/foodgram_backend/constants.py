# Ограничения для ингредиентов в рецепте
INGREDIENT_AMOUNT_MIN = 1
INGREDIENT_AMOUNT_MAX = 10000  # 10 кг максимум

# Временные рамки приготовления (в минутах)
COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 32000

# Параметры изображений
IMAGE_SIZE_LIMIT = 33  # Мб или другие единицы

# Пагинация
DEFAULT_PAGE_SIZE = 6
MAX_PAGE_SIZE = 100

# Ограничения длины текстовых полей
TEXT_LENGTH_SHORT = 50
TEXT_LENGTH_MEDIUM = 150
TEXT_LENGTH_MAX = 254
NAME_MAX_LENGTH = 150

# Для рецептов (используются в сериализаторах)
MIN_RECIPE_TIME = 1
MAX_RECIPE_TIME = 32000
