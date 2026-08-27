from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse

from apps.recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeIngredientGroup, RecipeStep, RecipeStepGroup, Unit
from apps.recipes.services.servings import coerce_servings, scale_nutrition, scale_quantity


class RecipeExportPdfTests(TestCase):
    def test_export_pdf_returns_pdf_response(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="draft")
        ingredient_group = RecipeIngredientGroup.objects.create(recipe=recipe, name="Main", order=0)
        step_group = RecipeStepGroup.objects.create(recipe=recipe, name="Method", order=0)
        ingredient = Ingredient.objects.create(name="Sugar")
        unit = Unit.objects.create(name="gram", type="weight", grams_per_unit=1)
        RecipeIngredient.objects.create(
            group=ingredient_group,
            ingredient=ingredient,
            quantity=250,
            unit=unit,
            order=0,
        )
        RecipeStep.objects.create(group=step_group, description="Mix well.", order=0)

        response = self.client.get(reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_pdf_accepts_servings_query_param(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="draft")
        response = self.client.get(
            reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug}),
            {"servings": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_servings_scaling_helpers_scale_values(self):
        nutrition = SimpleNamespace(
            per_serving_kcal=100,
            per_serving_protein=10,
            per_serving_fat=5,
            per_serving_carbs=20,
            per_serving_sugar=3,
            per_serving_salt=1,
        )

        self.assertEqual(coerce_servings("3", 4), 3)
        self.assertEqual(coerce_servings("2.5", 4), 2.5)
        self.assertAlmostEqual(coerce_servings("1/3", 4), 1 / 3)
        self.assertEqual(coerce_servings("1 1/2", 4), 1.5)
        self.assertEqual(coerce_servings("-1", 4), 4)
        self.assertEqual(coerce_servings("0", 4), 4)
        self.assertEqual(scale_quantity(250, 4, 2), 125)
        self.assertEqual(scale_quantity(250, 4, 2.5), 156.25)

        totals = scale_nutrition(nutrition, 2.5)
        self.assertEqual(totals.kcal, 250)
        self.assertEqual(totals.protein, 25)
        self.assertEqual(totals.carbs, 50)
