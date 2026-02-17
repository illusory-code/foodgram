from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from foodgram_backend.constants import (
    MAX_RECIPE_TIME,
    MIN_RECIPE_TIME,
    NAME_MAX_LENGTH,
)
from recipes.models import (
    FavoriteItem,
    Ingredient,
    Recipe,
    RecipeComponent,
    Tag,
)
from rest_framework import serializers
from users.models import FollowRelationship
from users.validators import (
    validate_first_name,
    validate_full_name,
    validate_username_field,
)

User = get_user_model()


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return CompactRecipeSerializer(instance.recipe).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = FavoriteItem
        fields = ('id', 'user', 'recipe')


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя."""

    first_name = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[validate_full_name, validate_first_name],
        required=True,
    )
    last_name = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[validate_full_name],
        required=True,
    )
    username = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[validate_username_field],
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

    def create(self, validated):
        try:
            new_user = User.objects.create_user(**validated)
            return new_user
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Запрещено использовать "me" как имя пользователя'
            )
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор данных пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    first_name = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[validate_full_name, validate_first_name],
    )
    last_name = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[validate_full_name],
    )
    username = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[validate_username_field],
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return FollowRelationship.objects.filter(
            subscriber=request.user,
            following=obj
        ).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField()
    author = UserDetailSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='components',
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteItem.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingListSerializer.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_RECIPE_TIME,
        max_value=MAX_RECIPE_TIME,
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""

    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_RECIPE_TIME,
        max_value=MAX_RECIPE_TIME,
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

    def _save_ingredients(self, recipe, ingredients_data):
        RecipeComponent.objects.bulk_create([
            RecipeComponent(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ])

    def create(self, validated):
        ingredients = validated.pop('ingredients')
        tags = validated.pop('tags')

        new_recipe = Recipe.objects.create(**validated)
        new_recipe.tags.set(tags)
        self._save_ingredients(new_recipe, ingredients)

        return new_recipe

    def update(self, instance, validated):
        ingredients = validated.pop('ingredients', None)
        tags = validated.pop('tags', None)

        instance = super().update(instance, validated)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.components.all().delete()
            self._save_ingredients(instance, ingredients)

        return instance

    def validate(self, data):
        tags_list = data.get('tags')
        if not tags_list:
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать минимум один тег'}
            )
        if len(tags_list) != len(set(tags_list)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться'}
            )

        ingredients_list = data.get('ingredients')
        if not ingredients_list:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать минимум один ингредиент'}
            )

        unique_ingredients = set()
        for item in ingredients_list:
            ing_id = item['id']
            if ing_id in unique_ingredients:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты должны быть уникальны'}
                )
            unique_ingredients.add(ing_id)

        if not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Изображение обязательно для загрузки'}
            )

        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class CompactRecipeSerializer(serializers.ModelSerializer):
    """Компактный сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AuthorSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор автора с рецептами для подписок."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user == obj:
            return False
        return FollowRelationship.objects.filter(
            subscriber=request.user,
            following=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.own_recipes.all()
        if limit:
            recipes_qs = recipes_qs[:int(limit)]
        return CompactRecipeSerializer(
            recipes_qs,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.own_recipes.count()


class SubscribeActionSerializer(serializers.ModelSerializer):
    """Сериализатор действия подписки."""

    class Meta:
        model = FollowRelationship
        fields = ('following', 'subscriber')

    def validate(self, attrs):
        request = self.context.get('request')
        if request.user == attrs['following']:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя'
            )
        if FollowRelationship.objects.filter(
            subscriber=request.user,
            following=attrs['following']
        ).exists():
            raise serializers.ValidationError(
                'Подписка уже оформлена'
            )
        return attrs

    def to_representation(self, instance):
        return AuthorSubscriptionSerializer(
            instance.following,
            context=self.context
        ).data


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор подписок."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and FollowRelationship.objects.filter(
                subscriber=request.user,
                following=obj
            ).exists()
        )

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.own_recipes.all()
        if limit:
            recipes_qs = recipes_qs[:int(limit)]
        return CompactRecipeSerializer(
            recipes_qs,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.own_recipes.count()
