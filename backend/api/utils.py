"""Вспомогательные функции для API."""


def generate_shopping_list_text(items):
    """
    Генерирует текст списка покупок на основе данных об ингредиентах.
        Args:
        items: QuerySet с агрегированными данными об ингредиентах
        Returns:
        str: Отформатированный текст списка покупок
    """
    lines = ['Список покупок:\n']

    for item in items:
        lines.append(
            f'{item["ingredient__name"]} — '
            f'{item["total_amount"]} '
            f'{item["ingredient__measurement_unit"]}'
        )

    return '\n'.join(lines)
