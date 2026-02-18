from foodgram_backend.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from rest_framework.pagination import PageNumberPagination


class PaginatedResponse(PageNumberPagination):
    """Настраиваемая пагинация для рецептов."""

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
