import io
import logging

from api.filters import IngredientNameFilter, RecipeFilter
from api.pagination import PaginatedResponse
from api.permissions import AuthorOrReadOnly
from api.serializers import (
    AuthorWithRecipesSerializer,
    CartSerializer,
    IngredientInfoSerializer,
    RecipeInputSerializer,
    RecipeOutputSerializer,
    ShortRecipeSerializer,
    SubscriptionListSerializer,
    TagInfoSerializer,
    UserInfoSerializer,
)
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
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)
User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """Контроллер управления рецептами."""

    queryset = Recipe.objects.all()
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
        qs = super().get_queryset()

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
                in_shopping_cart=Exists(in_cart_sq),
                is_favorite=Exists(liked_sq)
            )

        cart_filter = self.request.query_params.get('is_in_shopping_cart')
        if cart_filter is not None and user.is_authenticated:
            val = cart_filter.lower() in ('true', '1', 'yes')
            qs = qs.filter(in_shopping_cart=val)

        liked_filter = self.request.query_params.get('is_favorited')
        if liked_filter is not None and user.is_authenticated:
            val = liked_filter.lower() in ('true', '1', 'yes')
            qs = qs.filter(is_favorite=val)

        return qs

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if FavoriteItem.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteItem.objects.create(user=user, recipe=recipe)
            return Response(
                ShortRecipeSerializer(
                    recipe,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        fav_item = FavoriteItem.objects.filter(
            user=user,
            recipe=recipe
        ).first()
        if fav_item:
            fav_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт отсутствует в избранном'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            obj, created = ShoppingItem.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if created:
                return Response(
                    CartSerializer(obj).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': 'Рецепт уже в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item = ShoppingItem.objects.filter(
            user=user,
            recipe=recipe
        ).first()
        if cart_item:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт отсутствует в корзине'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        items = RecipeComponent.objects.filter(
            recipe__shopping_items__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        lines = ['Список покупок:\n']
        for item in items:
            lines.append(
                f'{item["ingredient__name"]} — '
                f'{item["total_amount"]} '
                f'{item["ingredient__measurement_unit"]}'
            )

        buffer = io.StringIO()
        buffer.write('\n'.join(lines))
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
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError({'error': f'Рецепт с ID {pk} не найден'})
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

    def get_queryset(self):
        qs = Ingredient.objects.all()
        name_query = self.request.query_params.get('name')
        if name_query:
            qs = qs.filter(name__istartswith=name_query)
        return qs


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
        )


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
            user.avatar.delete()
            user.avatar = None
            user.save()
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
            from users.models import FollowRelationship
            if FollowRelationship.objects.filter(
                subscriber=current_user,
                target=target_user
            ).exists():
                return Response(
                    {'error': 'Подписка уже оформлена'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FollowRelationship.objects.create(
                subscriber=current_user,
                target=target_user
            )
            return Response(
                AuthorWithRecipesSerializer(
                    target_user,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        from users.models import FollowRelationship
        sub = FollowRelationship.objects.filter(
            subscriber=current_user,
            target=target_user
        ).first()
        if sub:
            sub.delete()
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
        )
        page = self.paginate_queryset(qs)
        serializer = SubscriptionListSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class AvatarUpdateView(APIView):
    """Контроллер обновления аватара."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
