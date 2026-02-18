from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorOrReadOnly(BasePermission):
    """
    Доступ на запись только для автора объекта.
    Чтение разрешено всем.
    """

    def has_object_permission(self, request, view, target_obj):
        if request.method in SAFE_METHODS:
            return True
        return target_obj.author == request.user
