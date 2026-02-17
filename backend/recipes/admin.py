from django.contrib import admin
from django.utils.html import format_html
from recipes.models import (
    FavoriteItem,
    Ingredient,
    Recipe,
    RecipeComponent,
    ShoppingItem,
    Tag,
)


@admin.register(Ingredient)
class IngredientAdminConfig(admin.ModelAdmin):
    """Управление ингредиентами."""

    list_display = ('id', 'name', 'unit', 'recipes_count')
    search_fields = ('name',)
    list_filter = ('unit',)
    ordering = ('name',)

    def recipes_count(self, obj):
        return obj.recipecomponent_set.count()
    recipes_count.short_description = 'Кол-во рецептов'


class RecipeComponentInline(admin.TabularInline):
    """Инлайн для ингредиентов рецепта."""

    model = RecipeComponent
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdminConfig(admin.ModelAdmin):
    """Управление рецептами."""

    list_display = (
        'id',
        'title',
        'author',
        'cooking_time',
        'created',
        'favorites_count',
        'preview_image',
    )
    list_filter = ('tags', 'created', 'cooking_time')
    search_fields = ('title', 'text', 'author__username')
    readonly_fields = ('created',)
    filter_horizontal = ('tags',)
    inlines = [RecipeComponentInline]
    date_hierarchy = 'created'

    def favorites_count(self, obj):
        return obj.favoriteitem_set.count()
    favorites_count.short_description = 'В избранном'

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.image.url
            )
        return '—'
    preview_image.short_description = 'Фото'


@admin.register(Tag)
class TagAdminConfig(admin.ModelAdmin):
    """Управление тегами."""

    list_display = ('id', 'name', 'color_code', 'slug', 'display_color')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def display_color(self, obj):
        return format_html(
            '<span style="background: {};'
            'padding: 5px 10px; border-radius: 3px;">{}</span>',
            obj.color_code,
            obj.color_code
        )
    display_color.short_description = 'Цвет'


@admin.register(ShoppingItem)
class ShoppingItemAdminConfig(admin.ModelAdmin):
    """Управление списком покупок."""

    list_display = ('id', 'user', 'recipe', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'recipe__title')
    autocomplete_fields = ('user', 'recipe')


@admin.register(FavoriteItem)
class FavoriteItemAdminConfig(admin.ModelAdmin):
    """Управление избранным."""

    list_display = ('id', 'user', 'recipe', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'recipe__title')
    autocomplete_fields = ('user', 'recipe')


@admin.register(RecipeComponent)
class RecipeComponentAdminConfig(admin.ModelAdmin):
    """Управление составом рецептов."""

    list_display = ('id', 'recipe', 'ingredient', 'quantity')
    list_filter = ('recipe__tags',)
    search_fields = ('recipe__title', 'ingredient__name')
    autocomplete_fields = ('recipe', 'ingredient')
