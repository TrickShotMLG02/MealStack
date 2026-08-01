from datetime import timedelta
from pathlib import Path
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from apps.common.text_formatting import normalize_german, slugify
from apps.common.time import format_timedelta
from apps.recipes.models import (
    Ingredient,
    Recipe,
    RecipeImage,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeStep,
    RecipeStepGroup,
    Unit,
)


class CommonUtilityTests(TestCase):
    def test_format_timedelta_handles_empty_hours_and_minutes(self):
        self.assertEqual(format_timedelta(None), "—")
        self.assertEqual(format_timedelta(timedelta(minutes=45)), "45m")
        self.assertEqual(format_timedelta(timedelta(hours=2, minutes=5)), "2h 5m")

    def test_slugify_normalizes_german_characters_for_urls(self):
        self.assertEqual(normalize_german("Äpfel Öl süß"), "Aepfel Oel suess")
        self.assertEqual(slugify("Äpfel Öl süß"), "aepfel-oel-suess")


class ModelBehaviorTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_recipe_time_defaults_display_and_string(self):
        recipe = Recipe.objects.create(title="Cake", preparation_time=timedelta(minutes=10))

        self.assertEqual(str(recipe), "Cake")
        self.assertEqual(recipe.total_time, timedelta(minutes=10))
        self.assertEqual(recipe.total_time_display(), "10m")
        self.assertEqual(recipe.cooking_time, timedelta())
        self.assertEqual(recipe.resting_time, timedelta())

    def test_recipe_image_placeholders_and_existing_images(self):
        recipe = Recipe.objects.create(title="Cake")

        self.assertIn("placeholder", recipe.primary_or_placeholder)
        self.assertIn("placeholder", recipe.images_or_placeholder[0].image.url)

        image_name = "recipes/cake.jpg"
        image_path = Path(self.media_root) / image_name
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(b"not-real-image")
        RecipeImage.objects.create(
            recipe=recipe,
            image=ContentFile(b"not-real-image", name=image_name),
            is_primary=True,
        )

        self.assertIn("/media/recipes/", recipe.primary_or_placeholder)
        self.assertIn("/media/recipes/", recipe.images_or_placeholder[0].image.url)

    def test_recipe_images_missing_files_use_placeholder(self):
        recipe = Recipe.objects.create(title="Cake")
        RecipeImage.objects.create(recipe=recipe, image="recipes/missing.jpg", is_primary=True)

        self.assertIn("placeholder", recipe.primary_or_placeholder)
        self.assertIn("placeholder", recipe.images_or_placeholder[0].image.url)

    def test_unit_conversions_and_errors(self):
        flour = Ingredient.objects.create(name="Flour", density=0.6)
        gram = Unit.objects.create(name="gram", type="weight", grams_per_unit=1)
        cup = Unit.objects.create(name="cup", type="volume", ml_per_unit=240)
        piece = Unit.objects.create(name="piece", type="count", grams_per_unit=50)
        unknown = Unit.objects.create(name="mystery", type="mystery")

        self.assertEqual(str(gram), "gram")
        self.assertEqual(gram.to_grams(100), 100)
        self.assertEqual(cup.to_grams(2, flour), 288)
        self.assertEqual(piece.to_grams(3), 150)
        with self.assertRaises(ValueError):
            cup.to_grams(1)
        with self.assertRaises(ValueError):
            unknown.to_grams(1)

    def test_model_string_methods(self):
        recipe = Recipe.objects.create(title="Cake")
        ingredient = Ingredient.objects.create(name="Sugar", brand="SweetCo")
        unit = Unit.objects.create(name="gram", type="weight")
        ingredient_group = RecipeIngredientGroup.objects.create(recipe=recipe, name="Main", order=1)
        step_group = RecipeStepGroup.objects.create(recipe=recipe, name="Method", order=1)
        recipe_ingredient = RecipeIngredient.objects.create(
            group=ingredient_group,
            ingredient=ingredient,
            unit=unit,
            quantity=2,
            order=1,
        )
        step = RecipeStep.objects.create(group=step_group, description="Mix.", order=1)

        self.assertEqual(str(ingredient), "Sugar")
        self.assertIn("Main", str(ingredient_group))
        self.assertIn("Sugar", str(recipe_ingredient))
        self.assertIn("Method", str(step_group))
        self.assertEqual(str(step), "Step 1  (Method)")
