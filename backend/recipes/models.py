from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class RecipesQuerySet(models.QuerySet):
    def in_shopping_cart(self, user):
        return self.filter(in_shopping_carts__user=user)

    def is_favorited(self, user):
        return self.filter(in_favorites__user=user)


class RecipesManager(models.Manager):
    def get_queryset(self):
        return RecipesQuerySet(self.model, using=self._db)

    def in_shopping_cart(self, user):
        return self.get_queryset().in_shopping_cart(user)

    def is_favorited(self, user):
        return self.get_queryset().is_favorited(user)


class BaseModel(models.Model):
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class Ingredients(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=128, verbose_name="Название", db_index=True, unique=True
    )
    measurement_unit = models.CharField(max_length=64, verbose_name="Еденица измерения")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="recipes",
        blank=False,
        null=True,
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=256, blank=False, db_index=True, verbose_name="Название"
    )
    image = models.ImageField(upload_to="recipes/", verbose_name="Изображение", blank=True, null=True)
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name="Ингредиенты",
        related_name="recipes",
        through="RecipeIngredient",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления", validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(verbose_name="Дата публикации", auto_now_add=True)

    objects = RecipesManager()

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]
        unique_together = ("author", "name")

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связывающая рецепты и ингредиенты."""

    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE, null=False, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE, null=False)
    amount = models.PositiveSmallIntegerField(default=0, verbose_name="Количество")

    class Meta:
        verbose_name = "Рецепт-Ингредиент"
        verbose_name_plural = "Рецепт-Ингредиент-Список"

    def __str__(self):
        return f"В {self.recipe} содержится {self.ingredient} в количестве {self.ingredient.measurement_unit} {self.amount}."


class FavoriteRecipe(BaseModel):
    """Модель для избранных рецептов пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_recipes",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name="in_favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        unique_together = ("user", "recipe")


class ShoppingCart(BaseModel):
    """Модель для списка покупок пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name="in_shopping_carts",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        unique_together = ("user", "recipe")


class RecipeShortLink(models.Model):
    """Модель для коротких ссылок на рецепты."""

    recipe = models.OneToOneField(
        Recipes,
        on_delete=models.CASCADE,
        related_name="short_link",
        verbose_name="Рецепт",
    )
    short_hash = models.CharField(
        max_length=10, unique=True, verbose_name="Короткий хеш"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Короткая ссылка"
        verbose_name_plural = "Короткие ссылки"

    def __str__(self):
        return f"Ссылка на {self.recipe.name}: {self.short_hash}"
