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

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label='В избранном',
    )

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='В корзине',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр рецептов, находящихся в избранном у текущего пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_items__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр рецептов, находящихся в корзине у текущего пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_items__user=self.request.user)
        return queryset


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
