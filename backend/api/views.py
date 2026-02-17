import io
import logging

from api.filters import IngredientSearchFilter, RecipeFilterSet
from api.pagination import RecipePagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    AuthorSubscriptionSerializer,
    CompactRecipeSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingListSerializer,
    SubscriptionDetailSerializer,
    TagSerializer,
    UserDetailSerializer,
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
    """Управление рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_authenticated:
            cart_subquery = ShoppingItem.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            fav_subquery = FavoriteItem.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            queryset = queryset.annotate(
                in_cart=Exists(cart_subquery),
                is_fav=Exists(fav_subquery)
            )

        cart_param = self.request.query_params.get('is_in_shopping_cart')
        if cart_param is not None and user.is_authenticated:
            val = cart_param.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(in_cart=val)

        fav_param = self.request.query_params.get('is_favorited')
        if fav_param is not None and user.is_authenticated:
            val = fav_param.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_fav=val)

        return queryset

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
                    {'detail': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteItem.objects.create(user=user, recipe=recipe)
            return Response(
                CompactRecipeSerializer(
                    recipe,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        fav = FavoriteItem.objects.filter(
            user=user,
            recipe=recipe
        ).first()
        if fav:
            fav.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден в избранном'},
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
                    ShoppingListSerializer(obj).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item = ShoppingItem.objects.filter(
            user=user,
            recipe=recipe
        ).first()
        if item:
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден в корзине'},
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
            recipe__shoppingitem__user=user
        ).values(
            'ingredient__name',
            'ingredient__unit',
        ).annotate(
            total=Sum('quantity')
        ).order_by('ingredient__name')

        lines = ['Список покупок:\n']
        for item in items:
            lines.append(
                f'{item["ingredient__name"]} — '
                f'{item["total"]} '
                f'{item["ingredient__unit"]}'
            )

        buffer = io.StringIO()
        buffer.write('\n'.join(lines))
        buffer.seek(0)

        response = FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def short_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError({'error': f'Рецепт {pk} не найден'})
        short_url = request.build_absolute_uri(f'/r/{pk}/')
        return Response({'short-link': short_url})


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter
    pagination_class = None

    def get_queryset(self):
        qs = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            qs = qs.filter(name__istartswith=name)
        return qs


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class SubscriptionManageViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Управление подписками."""

    serializer_class = SubscriptionDetailSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecipePagination

    def get_queryset(self):
        return User.objects.filter(
            followers__follower=self.request.user
        )


class UserProfileViewSet(UserViewSet):
    """Управление профилями пользователей."""

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = RecipePagination

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = UserDetailSerializer(
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
    def manage_avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'error': 'Поле avatar обязательно'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserDetailSerializer(
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
        author = get_object_or_404(User, id=id)
        user = request.user

        if request.method == 'POST':
            from users.models import FollowRelationship
            if FollowRelationship.objects.filter(
                follower=user,
                following=author
            ).exists():
                return Response(
                    {'error': 'Уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FollowRelationship.objects.create(
                follower=user,
                following=author
            )
            return Response(
                AuthorSubscriptionSerializer(
                    author,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        from users.models import FollowRelationship
        sub = FollowRelationship.objects.filter(
            follower=user,
            following=author
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
    def list_subscriptions(self, request):
        qs = User.objects.filter(
            followers__follower=request.user
        )
        page = self.paginate_queryset(qs)
        serializer = SubscriptionDetailSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class AvatarManageView(APIView):
    """Управление аватаром."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
