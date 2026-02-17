from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram_backend.constants import (
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    INGREDIENT_AMOUNT_MAX,
    INGREDIENT_AMOUNT_MIN,
    TEXT_LENGTH_MAX,
)
from users.models import User


class TimestampMixin(models.Model):
    """Миксин для временных меток."""
    
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        abstract = True


class Ingredient(models.Model):
    """Ингредиент для рецептов."""

    name = models.CharField(
        max_length=TEXT_LENGTH_MAX,
        verbose_name='Название',
        db_index=True,
    )
    unit = models.CharField(
        max_length=50,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'unit'],
                name='unique_ingredient_combination'
            )
        ]
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.unit})'


class Tag(models.Model):
    """Тег для категоризации рецептов."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название',
        unique=True,
    )
    slug = models.SlugField(
        max_length=100,
        verbose_name='URL-идентификатор',
        unique=True,
    )
    color_code = models.CharField(
        max_length=7,
        verbose_name='HEX-код цвета',
        default='#49B64E',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(TimestampMixin):
    """Кулинарный рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='own_recipes',
        verbose_name='Автор',
    )
    title = models.CharField(
        max_length=TEXT_LENGTH_MAX,
        verbose_name='Название рецепта',
    )
    description = models.TextField(
        verbose_name='Описание приготовления',
    )
    image = models.ImageField(
        upload_to='recipes/%Y/%m/%d/',
        verbose_name='Изображение блюда',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин.)',
        validators=[
            MinValueValidator(COOKING_TIME_MIN),
            MaxValueValidator(COOKING_TIME_MAX),
        ],
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tagged_recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeComponent',
        related_name='used_in_recipes',
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

    def __str__(self):
        return self.title

    @property
    def favorites_count(self):
        return self.favoriteitem_set.count()

    @property
    def in_cart_count(self):
        return self.shoppingitem_set.count()


class RecipeComponent(models.Model):
    """Связь рецепта с ингредиентом (количество)."""

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
    quantity = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(INGREDIENT_AMOUNT_MIN),
            MaxValueValidator(INGREDIENT_AMOUNT_MAX),
        ],
    )

    class Meta:
        verbose_name = 'Компонент рецепта'
        verbose_name_plural = 'Компоненты рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe.title}: {self.ingredient.name} — {self.quantity}'


class UserRecipeRelation(TimestampMixin):
    """Абстрактная модель для связи пользователь-рецепт."""

    user = models.ForeignKey(
        User,
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
                name='%(class)s_unique_relation'
            )
        ]

    def __str__(self):
        return f'{self.user.username} ↔ {self.recipe.title}'


class FavoriteItem(UserRecipeRelation):
    """Избранные рецепты пользователя."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorite_items'


class ShoppingItem(UserRecipeRelation):
    """Рецепты в списке покупок."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Покупка'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping_items'
