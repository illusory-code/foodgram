from django_filters import rest_framework as filters
from django_filters.rest_framework import FilterSet
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтрация рецептов по критериям."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги',
        conjoined=False
    )

    author = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='ID автора',
    )

    is_favorited = filters.BooleanFilter(
        field_name='is_favorited',
        label='В избранном',
    )

    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        label='В корзине',
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']


class IngredientNameFilter(FilterSet):
    """Поиск ингредиентов по началу названия."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        label='Поисковый запрос',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
