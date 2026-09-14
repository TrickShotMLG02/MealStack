from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.recipes.admin.cuisine import CuisineAdmin
from apps.recipes.admin.ingredient import IngredientAdmin
from apps.recipes.admin.recipe import RecipeAdmin
from apps.recipes.admin.tag import TagAdmin
from apps.recipes.admin.unit import UnitAdmin
from apps.recipes.models import Cuisine, Ingredient, Recipe, Tag, Unit


class AdminFuzzySearchTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-secret123",
        )
        self.client.force_login(self.admin_user)

    def search(self, admin_class, model, term):
        admin_instance = admin_class(model, admin.site)
        results, may_have_duplicates = admin_instance.get_search_results(
            self.request,
            model.objects.all(),
            term,
        )
        return list(results), may_have_duplicates

    def test_ingredient_search_is_case_insensitive_and_partial(self):
        ingredient = Ingredient.objects.create(
            name="Farine Cuoco 00",
            generic_name="Wheat flour",
            brand="Cuoco",
        )
        Ingredient.objects.create(name="Tomato")

        for term in ("farine", "FARINE", "cuoco 00", "wheat flour"):
            with self.subTest(term=term):
                results, duplicates = self.search(IngredientAdmin, Ingredient, term)
                self.assertEqual(results, [ingredient])
                self.assertFalse(duplicates)

    def test_ingredient_search_falls_back_to_small_spelling_errors(self):
        ingredient = Ingredient.objects.create(name="Farine Cuoco 00")
        Ingredient.objects.create(name="Tomato")

        results, duplicates = self.search(IngredientAdmin, Ingredient, "farin cucco")

        self.assertEqual(results, [ingredient])
        self.assertFalse(duplicates)

    def test_ingredient_search_normalizes_accents_and_searches_metadata(self):
        ingredient = Ingredient.objects.create(
            name="Pizzakäse, gerieben",
            generic_name="Käse",
            brand="Müller",
        )

        for term in ("pizzakase", "kase", "muller"):
            with self.subTest(term=term):
                results, _ = self.search(IngredientAdmin, Ingredient, term)
                self.assertEqual(results, [ingredient])

    def test_fuzzy_search_does_not_return_unrelated_records(self):
        Ingredient.objects.create(name="Farine Cuoco 00")
        unrelated = Ingredient.objects.create(name="Tomato")

        results, _ = self.search(IngredientAdmin, Ingredient, "chocolate")

        self.assertNotIn(unrelated, results)
        self.assertEqual(results, [])

    def test_fuzzy_search_applies_to_recipe_related_admin_models(self):
        recipe = Recipe.objects.create(title="Spaghetti Napoli", status="draft")
        cuisine = Cuisine.objects.create(name="Italian")
        tag = Tag.objects.create(name="Weeknight")
        unit = Unit.objects.create(name="gram", type="weight")

        recipe_results, _ = self.search(RecipeAdmin, Recipe, "spagheti napoli")
        cuisine_results, _ = self.search(CuisineAdmin, Cuisine, "italan")
        tag_results, _ = self.search(TagAdmin, Tag, "weeknigt")
        unit_results, _ = self.search(UnitAdmin, Unit, "GRAM")

        self.assertEqual(recipe_results, [recipe])
        self.assertEqual(cuisine_results, [cuisine])
        self.assertEqual(tag_results, [tag])
        self.assertEqual(unit_results, [unit])

    def test_admin_autocomplete_uses_fuzzy_search_for_recipe_ingredients_and_components(self):
        ingredient = Ingredient.objects.create(name="Farine Cuoco 00")
        child_recipe = Recipe.objects.create(title="Tomato sauce", status="draft")

        ingredient_response = self.client.get(
            "/admin/autocomplete/",
            {
                "app_label": "recipes",
                "model_name": "recipeingredient",
                "field_name": "ingredient",
                "term": "farin cucco",
            },
        )
        recipe_response = self.client.get(
            "/admin/autocomplete/",
            {
                "app_label": "recipes",
                "model_name": "recipecomponent",
                "field_name": "child_recipe",
                "term": "tomto sauce",
            },
        )

        self.assertEqual(ingredient_response.status_code, 200)
        self.assertEqual(recipe_response.status_code, 200)
        self.assertEqual(ingredient_response.json()["results"][0]["id"], str(ingredient.pk))
        self.assertEqual(recipe_response.json()["results"][0]["id"], str(child_recipe.pk))
