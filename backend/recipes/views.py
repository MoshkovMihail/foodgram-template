from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import HttpResponseRedirect, HttpResponse
from .permissions import IsAuthorOrReadOnly
from collections import defaultdict
import hashlib
from .models import Recipes, Ingredients, FavoriteRecipe, RecipeShortLink, ShoppingCart
from .serializers import RecipeSerializer, IngredientSerializer
from users.serializers import RecipeShortSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ("author",)
    ordering = ("-pub_date",)
    permission_classes = [IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipes.objects.all()

        is_favorited = self.request.query_params.get("is_favorited")
        if is_favorited and self.request.user.is_authenticated:
            queryset = queryset.is_favorited(self.request.user)

        is_in_shopping_cart = self.request.query_params.get("is_in_shopping_cart")
        if is_in_shopping_cart and self.request.user.is_authenticated:
            queryset = queryset.in_shopping_cart(self.request.user)

        return queryset

    def __toggle_recipe_relation(self, request, pk, model_class):
        """
        Общий метод для добавления/удаления рецепта в избранное или список покупок
        """
        recipe = get_object_or_404(Recipes, pk=pk)
        user = request.user

        if request.method == "POST":
            if model_class.objects.filter(recipe=recipe, user=user).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            model_class.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            relation = model_class.objects.filter(recipe=recipe, user=user)

            if relation:
                relation.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        return self.__toggle_recipe_relation(request, pk, ShoppingCart)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        return self.__toggle_recipe_relation(request, pk, FavoriteRecipe)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)

        try:
            short_link_obj = RecipeShortLink.objects.get(recipe=recipe)
            short_hash = short_link_obj.short_hash
        except RecipeShortLink.DoesNotExist:
            hash_object = hashlib.md5(str(recipe.id).encode())
            short_hash = hash_object.hexdigest()[:6]

            RecipeShortLink.objects.create(recipe=recipe, short_hash=short_hash)

        base_url = request.build_absolute_uri("/").rstrip("/")
        short_link = f"{base_url}/s/{short_hash}/"

        return Response({"short-link": short_link})

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user

        shopping_cart_recipes = Recipes.objects.filter(
            in_shopping_carts__user=user
        ).prefetch_related("recipe_ingredients__ingredient")

        if not shopping_cart_recipes.exists():
            return Response(
                {"detail": "Ваш список покупок пуст"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ingredients_summary = defaultdict(
            lambda: {"name": "", "measurement_unit": "", "amount": 0}
        )

        for recipe in shopping_cart_recipes:
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                ingredient_id = ingredient.id

                ingredients_summary[ingredient_id]["name"] = ingredient.name
                ingredients_summary[ingredient_id][
                    "measurement_unit"
                ] = ingredient.measurement_unit
                ingredients_summary[ingredient_id]["amount"] += recipe_ingredient.amount

        shopping_list = []
        shopping_list.append("=== СПИСОК ПОКУПОК ===\n")
        shopping_list.append(f"Пользователь: {user.first_name} {user.last_name}\n")
        shopping_list.append(f"Рецептов в списке: {shopping_cart_recipes.count()}\n")
        shopping_list.append("=" * 50 + "\n\n")

        sorted_ingredients = sorted(
            ingredients_summary.items(), key=lambda x: x[1]["name"].lower()
        )

        for ingredient_id, data in sorted_ingredients:
            shopping_list.append(
                f"{data['name']} ({data['measurement_unit']}) — {data['amount']}\n"
            )

        shopping_list.append(f"\n{'='*50}\n")
        shopping_list.append("Список сгенерирован сервисом Foodgram\n")

        response = HttpResponse(
            "".join(shopping_list), content_type="text/plain; charset=utf-8"
        )
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'

        return response


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredients.objects.all()
        name = self.request.query_params.get("name", None)
        if name is not None:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


def redirect_short_link(request, short_hash):
    """
    Обработка коротких ссылок /s/{hash}/
    Перенаправляет на страницу рецепта
    """

    try:
        short_link_obj = RecipeShortLink.objects.select_related("recipe").get(
            short_hash=short_hash
        )
        recipe = short_link_obj.recipe
        frontend_url = f"{request.scheme}://{request.get_host()}/recipes/{recipe.id}/"
        return HttpResponseRedirect(frontend_url)
    except RecipeShortLink.DoesNotExist:

        return Response(status=status.HTTP_404_BAD_REQUEST)
