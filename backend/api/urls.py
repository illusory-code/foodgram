from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AvatarManageView,
    IngredientViewSet,
    RecipeViewSet,
    SubscriptionManageViewSet,
    TagViewSet,
    UserProfileViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register('users', UserProfileViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register(
    r'users/subscriptions',
    SubscriptionManageViewSet,
    basename='subscriptions'
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', AvatarManageView.as_view(), name='avatar'),
]
