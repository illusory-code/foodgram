from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorOrReadOnly(BasePermission):
    """
    Доступ на запись только для автора объекта.
    Чтение разрешено всем.
    """

    def has_object_permission(self, request, view, obj):
        """Проверка на уровне объекта."""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
