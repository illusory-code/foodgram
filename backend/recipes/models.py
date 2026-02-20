from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from foodgram_backend.constants import (
    COOKING_DURATION_MAX,
    COOKING_DURATION_MIN,
    INGREDIENT_QTY_MAX,
    INGREDIENT_QTY_MIN,
    INGREDIENT_UNIT_MAX_LENGTH,
    LONG_TEXT,
    TAG_COLOR_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)
from users.models import UserAccount


class TimeStampedModel(models.Model):
    """Абстрактная модель с временными метками."""

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    class Meta:
        abstract = True


class Ingredient(models.Model):
    """Ингредиент для рецептов."""

    name = models.CharField(
        max_length=LONG_TEXT,
        verbose_name='Название',
        db_index=True,
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """Тег для классификации рецептов."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        verbose_name='Название',
        unique=True,
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        verbose_name='Слаг',
        unique=True,
    )
    color_code = models.CharField(
        max_length=TAG_COLOR_MAX_LENGTH,
        verbose_name='HEX-цвет',
        default='#49B64E',
        help_text='Цвет тега для отображения в интерфейсе фронтенда'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(TimeStampedModel):
    """Кулинарный рецепт."""

    author = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=LONG_TEXT,
        verbose_name='Название',
    )
    text = models.TextField(
        verbose_name='Описание приготовления',
    )
    image = models.ImageField(
        upload_to='recipes/%Y/%m/%d/',
        verbose_name='Изображение',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[
            MinValueValidator(COOKING_DURATION_MIN),
            MaxValueValidator(COOKING_DURATION_MAX),
        ],
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeComponent',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['author', '-created']),
        ]
        default_related_name = 'recipes'

    def __str__(self):
        return self.name

    @property
    def likes_count(self):
        return self.favorite_items.count()

    @property
    def in_cart_count(self):
        return self.shopping_items.count()


class RecipeComponent(models.Model):
    """Связующая модель: рецепт + ингредиент + количество."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_entries',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(INGREDIENT_QTY_MIN),
            MaxValueValidator(INGREDIENT_QTY_MAX),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_component'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name}: {self.ingredient.name} — {self.amount}'


class UserRecipeBase(TimeStampedModel):
    """Абстрактная база для связи пользователь-рецепт."""

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique'
            )
        ]

    def __str__(self):
        return f'{self.user.username} — {self.recipe.name}'


class FavoriteItem(UserRecipeBase):
    """Избранные рецепты."""

    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorite_items'


class ShoppingItem(UserRecipeBase):
    """Рецепты в корзине покупок."""

    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Покупка'
        verbose_name_plural = 'Корзина покупок'
        default_related_name = 'shopping_items'
