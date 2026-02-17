from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import FilterSet
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilterSet(FilterSet):
    """Фильтрация рецептов по различным критериям."""

    tags = rest_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = rest_filters.NumberFilter(
        method='_filter_favorites',
        label='В избранном',
    )
    is_in_shopping_cart = rest_filters.BooleanFilter(
        method='_filter_cart',
        label='В корзине покупок',
    )
    author = rest_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='Автор рецепта',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def _filter_favorites(self, qs, name, val):
        current_user = self.request.user
        if current_user.is_authenticated and val:
            return qs.filter(in_favorites__user=current_user)
        return qs

    def _filter_cart(self, qs, name, val):
        current_user = self.request.user
        if current_user.is_authenticated and val:
            return qs.filter(in_cart__user=current_user)
        return qs


class IngredientSearchFilter(FilterSet):
    """Поиск ингредиентов по началу названия."""

    name = rest_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        label='Поиск по имени',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
