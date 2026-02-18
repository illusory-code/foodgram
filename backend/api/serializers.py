from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from foodgram_backend.constants import (
    MAX_COOKING_TIME,
    MIN_COOKING_TIME,
    USERNAME_MAX_LEN,
)
from recipes.models import (
    FavoriteItem,
    Ingredient,
    Recipe,
    RecipeComponent,
    ShoppingItem,
    Tag,
)
from rest_framework import serializers
from users.models import FollowRelationship
from users.validators import validate_name, validate_nickname

User = get_user_model()


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""

    class Meta:
        model = ShoppingItem
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe).data


class LikeSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = FavoriteItem
        fields = ('id', 'user', 'recipe')


class RegisterUserSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации пользователя."""

    first_name = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        validators=[validate_name],
        required=True,
    )
    last_name = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        validators=[validate_name],
        required=True,
    )
    username = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        validators=[validate_nickname],
        required=True,
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as error:
            raise serializers.ValidationError(str(error))

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Использовать "me" в качестве логина запрещено'
            )
        return value


class UserInfoSerializer(serializers.ModelSerializer):
    """Сериализатор информации о пользователе."""

    has_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    first_name = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        validators=[validate_name],
    )
    last_name = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        validators=[validate_name],
    )
    username = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        validators=[validate_nickname],
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'has_subscribed',
            'avatar',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def get_has_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return FollowRelationship.objects.filter(
            subscriber=request.user,
            target=obj
        ).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class TagInfoSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientInfoSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientOutputSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов при чтении рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeOutputSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта."""

    tags = TagInfoSerializer(many=True, read_only=True)
    image = Base64ImageField()
    author = UserInfoSerializer(read_only=True)
    ingredients = RecipeIngredientOutputSerializer(
        many=True,
        source='components',
        read_only=True,
    )
    is_liked = serializers.SerializerMethodField()
    is_in_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_liked',
            'is_in_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteItem.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingItem.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'amount')


class RecipeInputSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""

    ingredients = RecipeIngredientInputSerializer(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'cooking_time',
            'text',
            'tags',
            'ingredients',
            'image',
        )

    def _process_ingredients(self, recipe, items_data):
        RecipeComponent.objects.bulk_create([
            RecipeComponent(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in items_data
        ])

    def create(self, validated_data):
        items = validated_data.pop('ingredients')
        tags_list = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_list)
        self._process_ingredients(recipe, items)

        return recipe

    def update(self, instance, validated_data):
        items = validated_data.pop('ingredients', None)
        tags_list = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags_list is not None:
            instance.tags.set(tags_list)

        if items is not None:
            instance.components.all().delete()
            self._process_ingredients(instance, items)

        return instance

    def validate(self, data):
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Укажите хотя бы один тег'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны дублироваться'}
            )

        items = data.get('ingredients')
        if not items:
            raise serializers.ValidationError(
                {'ingredients': 'Укажите хотя бы один ингредиент'}
            )

        seen_ids = set()
        for item in items:
            ing_id = item['id']
            if ing_id in seen_ids:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты должны быть уникальны'}
                )
            seen_ids.add(ing_id)

        if not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Загрузите изображение блюда'}
            )

        return data

    def to_representation(self, instance):
        return RecipeOutputSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AuthorWithRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор автора с его рецептами (для подписок)."""

    has_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_total = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'has_subscribed',
            'recipes',
            'recipes_total',
            'avatar',
        )

    def get_has_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user == obj:
            return False
        return FollowRelationship.objects.filter(
            subscriber=request.user,
            target=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        qs = obj.created_recipes.all()
        if limit:
            qs = qs[:int(limit)]
        return ShortRecipeSerializer(
            qs,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_total(self, obj):
        return obj.created_recipes.count()


class FollowActionSerializer(serializers.ModelSerializer):
    """Сериализатор действия подписки/отписки."""

    class Meta:
        model = FollowRelationship
        fields = ('target', 'subscriber')

    def validate(self, attrs):
        request = self.context.get('request')
        if request.user == attrs['target']:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        if FollowRelationship.objects.filter(
            subscriber=request.user,
            target=attrs['target']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        return attrs

    def to_representation(self, instance):
        return AuthorWithRecipesSerializer(
            instance.target,
            context=self.context
        ).data


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Сериализатор списка подписок."""

    has_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_total = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'has_subscribed',
            'recipes',
            'recipes_total',
            'avatar',
        )

    def get_has_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and FollowRelationship.objects.filter(
                subscriber=request.user,
                target=obj
            ).exists()
        )

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        qs = obj.created_recipes.all()
        if limit:
            qs = qs[:int(limit)]
        return ShortRecipeSerializer(
            qs,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_total(self, obj):
        return obj.created_recipes.count()
