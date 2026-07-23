from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.recipes.admin.recipe import RecipeAdmin
from apps.recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeIngredientGroup, Unit
from apps.recipes.services.nutrition import update_recipe_nutrition


class RecipeNutritionServiceTests(TestCase):
    def test_update_recipe_nutrition_aggregates_related_ingredients(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="draft")
        group = RecipeIngredientGroup.objects.create(recipe=recipe, order=0)
        ingredient = Ingredient.objects.create(
            name="Sugar",
            kcal=400,
            fat=0,
            carbs=100,
            protein=0,
            salt=0,
        )
        unit = Unit.objects.create(name="gram", type="weight", grams_per_unit=1)
        RecipeIngredient.objects.create(
            group=group,
            ingredient=ingredient,
            quantity=250,
            unit=unit,
        )

        nutrition = update_recipe_nutrition(recipe)

        self.assertEqual(nutrition.total_kcal, 1000)
        self.assertEqual(nutrition.total_carbs, 250)
        self.assertEqual(nutrition.per_serving_kcal, 250)
        self.assertEqual(nutrition.per_serving_carbs, 62.5)


class RecipeAdminTests(TestCase):
    def test_save_related_refreshes_nutrition_after_inline_save(self):
        recipe = Recipe.objects.create(title="Cake", servings=2, status="draft")
        request = RequestFactory().post("/admin/recipes/recipe/1/change/")
        form = SimpleNamespace(instance=recipe, save_m2m=lambda: None)
        admin_instance = RecipeAdmin(Recipe, admin.site)

        with patch("apps.recipes.admin.recipe.update_recipe_nutrition") as mock_update:
            admin_instance.save_related(request, form, [], change=True)

        mock_update.assert_called_once_with(recipe)
