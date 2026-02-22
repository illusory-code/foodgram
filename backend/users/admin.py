from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import FollowRelationship, UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """Админ-панель пользовательских аккаунтов."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональные данные', {
            'fields': ('username', 'first_name', 'last_name', 'avatar')
        }),
        ('Права доступа', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    list_display = (
        'id', 'email', 'username', 'display_name',
        'is_active', 'recipes_created'
    )
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')

    @admin.display(description='Полное имя')
    def display_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip() or '—'

    @admin.display(description='Создано рецептов')
    def recipes_created(self, obj):
        return obj.recipes.count()


@admin.register(FollowRelationship)
class FollowRelationshipAdmin(admin.ModelAdmin):
    """Админ-панель подписок."""

    list_display = (
        'id', 'subscriber', 'target',
        'created_at', 'is_mutual_subscription'
    )
    list_filter = ('created_at',)
    search_fields = (
        'subscriber__email', 'target__email', 'subscriber__username'
    )
    autocomplete_fields = ('subscriber', 'target')
    date_hierarchy = 'created_at'

    @admin.display(description='Взаимная', boolean=True)
    def is_mutual_subscription(self, obj):
        return FollowRelationship.objects.filter(
            subscriber=obj.target,
            target=obj.subscriber
        ).exists()
