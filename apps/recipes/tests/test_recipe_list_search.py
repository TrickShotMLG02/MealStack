from django.test import TestCase
from django.urls import reverse

from apps.recipes.models import (
    Cuisine,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeNote,
    RecipeStep,
    RecipeStepGroup,
    Tag,
    Unit,
)


class RecipeListSearchTests(TestCase):
    def _create_recipe(self, title, *, cuisine_name=None, tag_names=None, ingredient_names=None, step_texts=None, note_text=None, author=None, source=None):
        recipe = Recipe.objects.create(
            title=title,
            servings=4,
            status="draft",
            author=author,
            source=source,
        )

        if cuisine_name:
            recipe.cuisine = Cuisine.objects.create(name=cuisine_name)
            recipe.save(update_fields=["cuisine"])

        for tag_name in tag_names or []:
            recipe.tags.add(Tag.objects.create(name=tag_name))

        if ingredient_names:
            group = RecipeIngredientGroup.objects.create(recipe=recipe, name="Main", order=0)
            unit = Unit.objects.create(name="gram", type="weight", grams_per_unit=1)
            for index, ingredient_name in enumerate(ingredient_names):
                ingredient = Ingredient.objects.create(name=ingredient_name)
                RecipeIngredient.objects.create(
                    group=group,
                    ingredient=ingredient,
                    quantity=10 + index,
                    unit=unit,
                    order=index,
                )

        if step_texts:
            group = RecipeStepGroup.objects.create(recipe=recipe, name="Method", order=0)
            for index, step_text in enumerate(step_texts):
                RecipeStep.objects.create(group=group, description=step_text, order=index)

        if note_text:
            RecipeNote.objects.create(recipe=recipe, content=note_text, ordering=0)

        return recipe

    def test_search_matches_titles_tags_and_cuisine(self):
        recipe = self._create_recipe(
            "Herb Pasta",
            cuisine_name="Italian",
            tag_names=["Dinner"],
        )
        self._create_recipe("Apple Pie")

        response = self.client.get(reverse("recipes:recipe_list"), {"q": "pasta"})
        self.assertContains(response, recipe.title)
        self.assertNotContains(response, "Apple Pie")

        response = self.client.get(reverse("recipes:recipe_list"), {"q": "italian"})
        self.assertContains(response, recipe.title)
        self.assertNotContains(response, "Apple Pie")

        response = self.client.get(reverse("recipes:recipe_list"), {"q": "dinner"})
        self.assertContains(response, recipe.title)
        self.assertNotContains(response, "Apple Pie")

        response = self.client.get(reverse("recipes:recipe_list"), {"q": "HERB PASTA"})
        self.assertContains(response, recipe.title)

        response = self.client.get(reverse("recipes:recipe_list"), {"q": "pstaa"})
        self.assertContains(response, recipe.title)

    def test_search_matches_ingredients_steps_notes_and_metadata(self):
        recipe = self._create_recipe(
            "Garden Soup",
            ingredient_names=["Basil"],
            step_texts=["Simmer gently."],
            note_text="Serve warm.",
            author="Marta",
            source="https://example.com/garden-soup",
        )
        self._create_recipe("Plain Rice")

        for query in ["basil", "simmer", "serve", "marta", "example.com"]:
            with self.subTest(query=query):
                response = self.client.get(reverse("recipes:recipe_list"), {"q": query})
                self.assertContains(response, recipe.title)
                self.assertNotContains(response, "Plain Rice")

    def test_search_returns_unique_recipes_for_multi_match_queries(self):
        recipe = self._create_recipe(
            "Pesto Pasta",
            cuisine_name="Italian",
            tag_names=["Basil"],
            ingredient_names=["Basil"],
        )

        response = self.client.get(reverse("recipes:recipe_list"), {"q": "basil"})
        results = list(response.context["recipes"])

        self.assertEqual(results, [recipe])

    def test_search_suggestions_return_useful_matches(self):
        recipe = self._create_recipe(
            "Garden Soup",
            cuisine_name="Italian",
            tag_names=["Dinner"],
            ingredient_names=["Basil"],
        )

        response = self.client.get(reverse("recipes:recipe_search_suggestions"), {"q": "basi"})
        self.assertEqual(response.status_code, 200)

        payload = response.json()["suggestions"]
        labels = [item["label"] for item in payload]

        self.assertIn(recipe.title, labels)
        self.assertIn("Basil", labels)
