from dataclasses import dataclass
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.recipes.importers.recipes.base import (
    BaseRecipeImporter,
    BaseRecipeScraperImporter,
    RecipeImageImportError,
    _hostname_matches_base_domain,
)
from apps.recipes.models import Cuisine, Recipe, RecipeIngredient, RecipeStep, Tag


@dataclass
class FakeIngredientGroup:
    purpose: str
    ingredients: list[str]


class FakeScraper:
    def __init__(
        self,
        *,
        title=" Imported Cake ",
        yields="Serves 4",
        prep_time=15,
        cook_time=30,
        author="Long Author",
        ingredients=None,
        ingredient_groups=None,
        instructions=None,
        keywords=None,
        image="",
        cuisine="Italian",
    ):
        self._title = title
        self._yields = yields
        self._prep_time = prep_time
        self._cook_time = cook_time
        self._author = author
        self._ingredients = ingredients or ["100g flour", "2 eggs"]
        self._ingredient_groups = ingredient_groups
        self._instructions = instructions or ["Method", "mix ingredients well", "bake until set"]
        self._keywords = keywords or ["Dessert", " Cake ", ""]
        self._image = image
        self._cuisine = cuisine

    def title(self):
        return self._title

    def yields(self):
        return self._yields

    def prep_time(self):
        return self._prep_time

    def cook_time(self):
        return self._cook_time

    def author(self):
        return self._author

    def ingredients(self):
        return self._ingredients

    def ingredient_groups(self):
        if self._ingredient_groups is None:
            raise AttributeError("no grouped ingredients")
        return self._ingredient_groups

    def instructions_list(self):
        return self._instructions

    def keywords(self):
        return self._keywords

    def image(self):
        return self._image

    def cuisine(self):
        return self._cuisine

    def to_json(self, **kwargs):
        return {"title": self._title, **kwargs}


class RaisingScraper(FakeScraper):
    def title(self):
        raise RuntimeError("title unavailable")

    def yields(self):
        raise RuntimeError("yield unavailable")

    def prep_time(self):
        raise RuntimeError("prep unavailable")

    def cook_time(self):
        raise RuntimeError("cook unavailable")

    def author(self):
        raise RuntimeError("author unavailable")

    def image(self):
        raise RuntimeError("image unavailable")

    def cuisine(self):
        raise RuntimeError("cuisine unavailable")


class TestScraperImporter(BaseRecipeScraperImporter):
    site_name = "Test Site"
    default_ingredient_group_name = "Ingredients"
    default_step_group_name = "Steps"
    base_domain = "example.com"


class RecipeImporterTests(TestCase):
    def test_hostname_matches_base_domain_and_subdomains(self):
        self.assertTrue(_hostname_matches_base_domain("example.com", "example.com"))
        self.assertTrue(_hostname_matches_base_domain("cdn.example.com", "example.com"))
        self.assertTrue(_hostname_matches_base_domain("EXAMPLE.COM.", "example.com"))
        self.assertFalse(_hostname_matches_base_domain("evil-example.com", "example.com"))
        self.assertFalse(_hostname_matches_base_domain(None, "example.com"))

    def test_base_importer_helpers_parse_simple_ingredients(self):
        self.assertEqual(BaseRecipeImporter.normalize_ingredient_name("Egg(s)"), "Egg")
        self.assertEqual(BaseRecipeImporter.normalize_ingredient("2 cup flour"), (2.0, "cup", "flour"))
        self.assertEqual(BaseRecipeImporter.normalize_ingredient("salt"), (1, "", "salt"))

        with self.assertRaises(NotImplementedError):
            BaseRecipeImporter.normalize_quantity(1, "cup")

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_creates_recipe_payload(self, scrape_me, update_nutrition):
        scrape_me.return_value = FakeScraper()

        recipe = TestScraperImporter("https://example.com/recipe").import_recipe()

        self.assertEqual(recipe.title, "Imported Cake")
        self.assertEqual(recipe.servings, 4)
        self.assertEqual(recipe.preparation_time.total_seconds(), 15 * 60)
        self.assertEqual(recipe.cooking_time.total_seconds(), 30 * 60)
        self.assertEqual(recipe.author, "Long Author")
        self.assertEqual(recipe.status, "published")
        self.assertEqual(recipe.cuisine.name, "Italian")
        self.assertEqual(Tag.objects.filter(name="Dessert").count(), 1)
        self.assertEqual(recipe.recipeingredientgroup_set.get().name, "Ingredients")
        self.assertEqual(RecipeIngredient.objects.count(), 2)
        self.assertEqual(RecipeStep.objects.count(), 2)
        update_nutrition.assert_called_once_with(recipe)

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_handles_grouped_ingredients_and_step_groups(self, scrape_me, update_nutrition):
        scrape_me.return_value = FakeScraper(
            ingredient_groups=[
                FakeIngredientGroup("", ["1 cup milk"]),
                FakeIngredientGroup("Topping", ["2 tbsp sugar"]),
            ],
            instructions=["Prep", "whisk until smooth", "Bake", "bake until set"],
            cuisine="",
        )

        recipe = TestScraperImporter("https://example.com/grouped").import_recipe()

        self.assertEqual(
            list(recipe.recipeingredientgroup_set.order_by("order").values_list("name", flat=True)),
            ["Ingredients 1", "Topping"],
        )
        self.assertEqual(
            list(recipe.recipestepgroup_set.order_by("order").values_list("name", flat=True)),
            ["Prep", "Bake"],
        )
        self.assertFalse(Cuisine.objects.exists())
        update_nutrition.assert_called_once_with(recipe)

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_clears_existing_payload_on_reimport(self, scrape_me, update_nutrition):
        scrape_me.side_effect = [
            FakeScraper(ingredients=["100g flour"], keywords=["Old"]),
            FakeScraper(title="Updated", ingredients=["200g sugar"], keywords=["New"]),
        ]

        importer = TestScraperImporter("https://example.com/reimport")
        first_recipe = importer.import_recipe()
        second_recipe = TestScraperImporter("https://example.com/reimport").import_recipe()

        self.assertEqual(first_recipe.pk, second_recipe.pk)
        second_recipe.refresh_from_db()
        self.assertEqual(second_recipe.title, "Updated")
        self.assertEqual(RecipeIngredient.objects.count(), 1)
        self.assertTrue(second_recipe.tags.filter(name="New").exists())
        self.assertFalse(second_recipe.tags.filter(name="Old").exists())
        self.assertEqual(update_nutrition.call_count, 2)

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_safe_fallbacks(self, scrape_me, update_nutrition):
        scraper = FakeScraper(
            title=None,
            yields="many",
            prep_time="soon",
            cook_time=None,
            author=123,
            ingredients=[],
            instructions=[],
            keywords=None,
            cuisine=None,
        )
        scrape_me.return_value = scraper

        recipe = TestScraperImporter("https://example.com/fallback").import_recipe()

        self.assertEqual(recipe.title, "Test Site")
        self.assertEqual(recipe.servings, 1)
        self.assertEqual(recipe.preparation_time.total_seconds(), 0)
        self.assertEqual(recipe.cooking_time.total_seconds(), 0)
        self.assertEqual(recipe.author, "123")
        update_nutrition.assert_called_once_with(recipe)

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_handles_scraper_method_exceptions(self, scrape_me, update_nutrition):
        scrape_me.return_value = RaisingScraper(ingredients=["1 cup milk"], instructions=["mix"])

        recipe = TestScraperImporter("https://example.com/raising").import_recipe()

        self.assertEqual(recipe.title, "Test Site")
        self.assertEqual(recipe.servings, 1)
        self.assertEqual(recipe.author, "")
        self.assertEqual(RecipeIngredient.objects.count(), 1)
        update_nutrition.assert_called_once_with(recipe)

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.BaseRecipeImporter.attach_image")
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_attempts_image_attachment(self, scrape_me, attach_image, update_nutrition):
        scrape_me.return_value = FakeScraper(image="https://example.com/image.jpg")

        recipe = TestScraperImporter("https://example.com/image").import_recipe()

        attach_image.assert_called_once_with(
            recipe,
            "https://example.com/image.jpg",
            primary=True,
            ordering=0,
            base_domain="example.com",
        )

    @patch("apps.recipes.importers.recipes.base.update_recipe_nutrition")
    @patch("apps.recipes.importers.recipes.base.BaseRecipeImporter.attach_image", side_effect=RecipeImageImportError("bad"))
    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_ignores_image_import_errors(self, scrape_me, attach_image, update_nutrition):
        scrape_me.return_value = FakeScraper(image="https://example.com/bad.jpg")

        recipe = TestScraperImporter("https://example.com/bad-image").import_recipe()

        self.assertEqual(recipe.title, "Imported Cake")
        attach_image.assert_called_once()

    @patch("apps.recipes.importers.recipes.base.scrape_me")
    def test_scraper_importer_to_json_delegates_to_scraper(self, scrape_me):
        scrape_me.return_value = FakeScraper()

        self.assertEqual(
            TestScraperImporter("https://example.com/json").to_json(indent=2),
            {"title": " Imported Cake ", "indent": 2},
        )
