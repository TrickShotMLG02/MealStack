from django.test import TestCase
from django.urls import reverse

from apps.recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeIngredientGroup, RecipeStep, RecipeStepGroup, Unit


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
