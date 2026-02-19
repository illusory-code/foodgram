import io
import logging

from api.filters import IngredientNameFilter, RecipeFilter
from api.pagination import PaginatedResponse
from api.permissions import AuthorOrReadOnly
from api.serializers import (
    AuthorWithRecipesSerializer,
    CartSerializer,
    IngredientInfoSerializer,
    LikeSerializer,
    RecipeInputSerializer,
    RecipeOutputSerializer,
    SubscriptionListSerializer,
    TagInfoSerializer,
    UserInfoSerializer,
)
from api.utils import generate_shopping_list_text
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (
    FavoriteItem,
    Ingredient,
    Recipe,
    RecipeComponent,
    ShoppingItem,
    Tag,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import FollowRelationship

logger = logging.getLogger(__name__)
User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """Контроллер управления рецептами."""

    permission_classes = [AuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PaginatedResponse

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeInputSerializer
        return RecipeOutputSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        qs = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'components__ingredient'
        )

        if user.is_authenticated:
            in_cart_sq = ShoppingItem.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            liked_sq = FavoriteItem.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            qs = qs.annotate(
                is_in_cart=Exists(in_cart_sq),
                is_liked=Exists(liked_sq)
            )
        else:
            qs = qs.annotate(
                is_in_cart=Exists(ShoppingItem.objects.none()),
                is_liked=Exists(FavoriteItem.objects.none())
            )

        return qs

    def _handle_favorite_cart(self, request, pk, model, serializer_class):
        """Обобщённый метод для работы с избранным и корзиной."""
        user = request.user

        if request.method == 'POST':
            # Используем get_object() непосредственно при создании
            obj, created = model.objects.get_or_create(
                user=user,
                recipe=self.get_object()
            )
            if created:
                serializer = serializer_class(
                    obj,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # DELETE method - используем get_object() непосредственно в фильтре
        deleted, _ = model.objects.filter(
            user=user,
            recipe=self.get_object()
        ).delete()

        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт отсутствует'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def add_favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        return self._handle_favorite_cart(
            request, pk, FavoriteItem, LikeSerializer
        )

    @add_favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        return self._handle_favorite_cart(
            request, pk, FavoriteItem, LikeSerializer
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def add_to_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        return self._handle_favorite_cart(
            request, pk, ShoppingItem, CartSerializer
        )

    @add_to_cart.mapping.delete
    def delete_from_cart(self, request, pk=None):
        """Удаление рецепта из корзины."""
        return self._handle_favorite_cart(
            request, pk, ShoppingItem, CartSerializer
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        user = request.user
        items = RecipeComponent.objects.filter(
            recipe__shopping_items__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        file_content = generate_shopping_list_text(items)

        buffer = io.StringIO()
        buffer.write(file_content)
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        get_object_or_404(Recipe, pk=pk)
        short_url = request.build_absolute_uri(f'/r/{pk}/')
        return Response({'short-link': short_url})


class IngredientListView(viewsets.ReadOnlyModelViewSet):
    """Контроллер просмотра ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientInfoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientNameFilter
    pagination_class = None


class TagListView(viewsets.ReadOnlyModelViewSet):
    """Контроллер просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagInfoSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class SubscriptionViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Контроллер управления подписками."""

    serializer_class = SubscriptionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PaginatedResponse

    def get_queryset(self):
        return User.objects.filter(
            followers__subscriber=self.request.user
        ).prefetch_related('recipes')


class UserAccountViewSet(UserViewSet):
    """Контроллер управления пользователями."""

    queryset = User.objects.all()
    serializer_class = UserInfoSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PaginatedResponse

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = UserInfoSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'error': 'Поле avatar обязательно для заполнения'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserInfoSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': user.avatar.url if user.avatar else None}
            )

        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        target_user = get_object_or_404(User, id=id)
        current_user = request.user

        if request.method == 'POST':
            _, created = FollowRelationship.objects.get_or_create(
                subscriber=current_user,
                target=target_user
            )
            if created:
                return Response(
                    AuthorWithRecipesSerializer(
                        target_user,
                        context={'request': request}
                    ).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Подписка уже оформлена'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted, _ = FollowRelationship.objects.filter(
            subscriber=current_user,
            target=target_user
        ).delete()

        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Подписка не найдена'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        qs = User.objects.filter(
            followers__subscriber=request.user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(qs)
        serializer = SubscriptionListSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
