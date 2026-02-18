"""
URL configuration for foodgram project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


def build_url_patterns():
    """Формирование URL-конфигурации проекта."""
    patterns = [
        path('admin/', admin.site.urls),
        path('api/', include('api.urls', namespace='api')),
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
