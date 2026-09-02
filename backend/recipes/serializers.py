from rest_framework import serializers
from users.serializers import UserSerializer

from .models import (
    Recipes,
    Ingredients,
    FavoriteRecipe,
    ShoppingCart,
    RecipeIngredient,
)
from core.serializers import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ("id", "name", "measurement_unit")


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredients.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientReadSerializer(source="recipe_ingredients", many=True)
    author = UserSerializer(read_only=True, many=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipes
        fields = (
            "id",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "author",
        )
        read_only = ("id", "author")

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один ингредиент.")
        
        ingredient_ids = [item['ingredient'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться.")
        
        for item in value:
            if item['amount'] <= 0:
                raise serializers.ValidationError("Количество ингредиента должно быть больше 0.")
        
        return value

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError("Время приготовления должно быть больше 0.")
        return value

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Название рецепта не может быть пустым.")
        return value.strip()

    def validate(self, data):
        if 'ingredients' in data and not data['ingredients']:
            raise serializers.ValidationError({
                'ingredients': 'Рецепт должен содержать хотя бы один ингредиент.'
            })
        
        if self.instance and 'ingredients' not in data:
            raise serializers.ValidationError({
                'ingredients': 'Поле ingredients обязательно для заполнения.'
            })
        
        if not self.instance and 'image' not in data:
            raise serializers.ValidationError({
                'image': 'Поле image обязательно для заполнения.'
            })
        
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipes.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"],
                amount=ingredient_data["amount"],
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        if "ingredients" in validated_data:
            RecipeIngredient.objects.filter(recipe=instance).delete()

            ingredients_data = validated_data.pop("ingredients")
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data["ingredient"],
                    amount=ingredient_data["amount"],
                )

        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(instance, context=self.context)
        return serializer.data
