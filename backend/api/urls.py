from api.views import (
    IngredientListView,
    RecipeViewSet,
    SubscriptionViewSet,
    TagListView,
    UserAccountViewSet,
)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('users', UserAccountViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientListView, basename='ingredients')
router.register('tags', TagListView, basename='tags')
router.register(
    r'users/subscriptions',
    SubscriptionViewSet,
    basename='subscriptions'
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
