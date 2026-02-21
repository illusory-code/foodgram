import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponseRedirect
from django.urls import include, path
from django.views.generic import TemplateView

from recipes.models import Recipe


def short_link_redirect(request, pk):
    """Редирект с короткой ссылки на страницу рецепта."""
    try:
        Recipe.objects.get(pk=pk)
        return HttpResponseRedirect(f'/recipes/{pk}/')
    except Recipe.DoesNotExist:
        return HttpResponseRedirect('/not-found/')


def serve_openapi_schema(request):
    """Вьюшка для отдачи openapi-schema.yml"""
    file_path = os.path.join(
        settings.BASE_DIR.parent,
        'nginx/docs/openapi-schema.yml')
    return FileResponse(
        open(file_path, 'rb'),
        content_type='application/yaml'
    )


def build_url_patterns():
    """Формирование URL-конфигурации проекта."""
    patterns = [
        path('admin/', admin.site.urls),
        path('api/', include('api.urls', namespace='api')),
        path('api/docs/', TemplateView.as_view(
            template_name='redoc.html',
            extra_context={'schema_url': '/api/openapi-schema.yml'}
        ), name='redoc'),
        path(
            'api/openapi-schema.yml',
            serve_openapi_schema,
            name='openapi-schema'
        ),
        path('r/<int:pk>/', short_link_redirect, name='short-link'),
    ]
    return patterns


def add_media_urls(patterns):
    """Добавление URL для медиа-файлов в режиме разработки."""
    if settings.DEBUG:
        return patterns + static(
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT
        )
    return patterns


urlpatterns = add_media_urls(build_url_patterns())
