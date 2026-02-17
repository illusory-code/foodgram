from rest_framework.pagination import PageNumberPagination

from foodgram_backend.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE_LIMIT,
)


class RecipePagination(PageNumberPagination):
    """Пагинация с настраиваемым размером страницы."""

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE_LIMIT
