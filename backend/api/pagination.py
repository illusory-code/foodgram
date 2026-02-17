from foodgram_backend.constants import DEFAULT_PAGE_SIZE, PAGINATION_MAX
from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Пагинация с настраиваемым размером страницы."""

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = PAGINATION_MAX
