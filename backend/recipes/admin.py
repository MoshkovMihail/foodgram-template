from django.contrib import admin

from .models import (
    Ingredients,
    Recipes,
    FavoriteRecipe,
    ShoppingCart,
    RecipeIngredient,
    RecipeShortLink,
)


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ("name", "cooking_time", "pub_date")
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "added_at")
    list_filter = ("user", "recipe")
    search_fields = ("user", "recipe")


@admin.register(RecipeIngredient)
class RecipeIngridientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    list_filter = (
        "recipe",
        "ingredient",
    )
    search_fields = (
        "recipe",
        "ingredient",
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "added_at")
    list_filter = ("user", "recipe", "added_at")
    search_fields = ("user", "recipe", "added_at")


@admin.register(RecipeShortLink)
class RecipeShortLinkAdmin(admin.ModelAdmin):
    list_display = ("recipe", "short_hash", "created_at")
    list_filter = ("created_at",)
    search_fields = ("recipe__name", "short_hash")
    readonly_fields = ("short_hash", "created_at")

    def has_add_permission(self, request):
        return False


admin.site.empty_value_display = "Не задано"
