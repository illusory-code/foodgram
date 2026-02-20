from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorOrReadOnly(BasePermission):
    """
    Доступ на запись только для автора объекта.
    Чтение разрешено всем.
    """

    def has_permission(self, request, view):
        """Проверка на уровне запроса."""
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, target_obj):
        """Проверка на уровне объекта."""
        if request.method in SAFE_METHODS:
            return True
        return target_obj.author == request.user
