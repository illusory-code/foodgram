from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import FollowRelationship, UserAccount


@admin.register(UserAccount)
class AccountAdmin(BaseUserAdmin):
    """Управление пользовательскими аккаунтами."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Персональная информация'), {
            'fields': ('username', 'first_name', 'last_name', 'avatar')
        }),
        (_('Права доступа'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    list_display = (
        'id', 'email', 'username', 'full_name',
        'is_active', 'recipe_count'
    )
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')

    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip() or '—'
    full_name.short_description = 'Полное имя'

    def recipe_count(self, obj):
        return obj.own_recipes.count()
    recipe_count.short_description = 'Рецептов'


@admin.register(FollowRelationship)
class FollowAdmin(admin.ModelAdmin):
    """Управление подписками пользователей."""

    list_display = (
        'id', 'follower', 'following',
        'created_at', 'is_mutual'
    )
    list_filter = ('created_at',)
    search_fields = (
        'follower__email', 'following__email', 'follower__username'
    )
    autocomplete_fields = ('follower', 'following')
    date_hierarchy = 'created_at'

    def is_mutual(self, obj):
        return FollowRelationship.objects.filter(
            follower=obj.following,
            following=obj.follower
        ).exists()
    is_mutual.boolean = True
    is_mutual.short_description = 'Взаимная подписка'
