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
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit', 'usage_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    ordering = ('name',)

    @admin.display(description='Использован в рецептах')
    def usage_count(self, obj):
        """Возвращает количество использований ингредиента в рецептах."""
        return obj.recipe_entries.count()


class ComponentInline(admin.TabularInline):
    """Инлайн-редактор ингредиентов рецепта."""

    model = RecipeComponent
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель рецептов."""

    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'created',
        'likes_count',
        'image_preview',
    )
    list_filter = ('tags', 'created', 'cooking_time')
    search_fields = ('name', 'text', 'author__username')
    readonly_fields = ('created',)
    filter_horizontal = ('tags',)
    inlines = [ComponentInline]
    date_hierarchy = 'created'

    @admin.display(description='В избранном')
    def likes_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_items.count()

    @admin.display(description='Превью')
    def image_preview(self, obj):
        """Возвращает HTML-код для превью изображения."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.image.url
            )
        return '—'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-панель тегов."""

    list_display = ('id', 'name', 'color_code', 'slug', 'color_preview')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    @admin.display(description='Цвет')
    def color_preview(self, obj):
        """Возвращает цветовой превью тега."""
        return format_html(
            '<span style="background: {}; padding: 5px 10px; '
            'border-radius: 3px; color: white;">{}</span>',
            obj.color_code,
            obj.color_code
        )


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    """Админ-панель списка покупок."""

    list_display = ('id', 'user', 'recipe', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')


@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    """Админ-панель избранного."""

    list_display = ('id', 'user', 'recipe', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')


@admin.register(RecipeComponent)
class RecipeComponentAdmin(admin.ModelAdmin):
    """Админ-панель компонентов рецептов."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe__tags',)
    search_fields = ('recipe__name', 'ingredient__name')
    autocomplete_fields = ('recipe', 'ingredient')
