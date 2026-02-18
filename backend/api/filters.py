from django_filters import rest_framework as filters
from django_filters.rest_framework import FilterSet
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтрация рецептов по критериям."""

    tag_slugs = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги',
    )
    liked_by_user = filters.NumberFilter(
        method='_filter_liked',
        label='В избранном',
    )
    in_user_cart = filters.BooleanFilter(
        method='_filter_in_cart',
        label='В корзине',
    )
    creator_id = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='ID автора',
    )

    class Meta:
        model = Recipe
        fields = ('tag_slugs', 'creator_id')

    def _filter_liked(self, queryset, field_name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorite_items__user=user)
        return queryset

    def _filter_in_cart(self, queryset, field_name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shopping_items__user=user)
        return queryset


class IngredientNameFilter(FilterSet):
    """Поиск ингредиентов по началу названия."""

    search_term = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        label='Поисковый запрос',
    )

    class Meta:
        model = Ingredient
        fields = ('search_term',)
