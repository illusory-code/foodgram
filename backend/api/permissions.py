from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorOrReadOnly(BasePermission):
    """
    Доступ на запись только для автора объекта.
    Чтение разрешено всем.
    """

    def has_object_permission(self, request, view, target_obj):
        return (
            request.method in SAFE_METHODS
            or target_obj.author == request.user
        )
