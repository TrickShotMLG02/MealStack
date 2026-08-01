from io import StringIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.recipes.importers.ingredients.base import EANNotFound
from apps.recipes.management.commands.SeedCommand import SeedCommand
from apps.recipes.management.commands import ingredient_importer, recipe_importer, seed_all
from apps.recipes.management.commands.seed_admin_user import Command as SeedAdminUserCommand
from apps.recipes.management.commands.seed_ingredients import Command as SeedIngredientsCommand
from apps.recipes.management.commands.seed_units import Command as SeedUnitsCommand
from apps.recipes.models import Ingredient, Recipe, Unit


class ImporterCommandTests(TestCase):
    def test_ingredient_importer_requires_ean(self):
        with self.assertRaises(CommandError):
            call_command("ingredient_importer")

    def test_ingredient_importer_rejects_unknown_importer(self):
        with self.assertRaises(CommandError):
            call_command("ingredient_importer", "123", importer_name="missing")

    def test_ingredient_importer_reports_missing_ean(self):
        importer_cls = Mock()
        importer_cls.return_value.import_ingredient.side_effect = EANNotFound("123")

        with patch.dict(ingredient_importer.Command.SUPPORTED_IMPORTERS, {"fake": importer_cls}):
            with self.assertRaises(CommandError) as context:
                call_command("ingredient_importer", "123", importer_name="fake")

        self.assertIn("Product not found for EAN: 123", str(context.exception))

    def test_ingredient_importer_success(self):
        ingredient = Ingredient.objects.create(ean="123", name="Milk")
        importer_cls = Mock()
        importer_cls.return_value.import_ingredient.return_value = ingredient
        output = StringIO()

        with patch.dict(ingredient_importer.Command.SUPPORTED_IMPORTERS, {"fake": importer_cls}):
            call_command("ingredient_importer", "123", importer_name="fake", stdout=output)

        importer_cls.assert_called_once_with(ean="123")
        self.assertIn("Imported ingredient 'Milk'", output.getvalue())

    def test_recipe_importer_requires_url(self):
        with self.assertRaises(CommandError):
            call_command("recipe_importer")

    def test_recipe_importer_rejects_unmatched_url(self):
        with patch("apps.recipes.management.commands.recipe_importer.get_recipe_importers", return_value=[]):
            with self.assertRaises(CommandError):
                call_command("recipe_importer", "https://example.com/recipe")

    def test_recipe_importer_rejects_unknown_named_importer(self):
        with self.assertRaises(CommandError):
            call_command("recipe_importer", "https://example.com/recipe", importer_name="missing")

    def test_recipe_importer_rejects_url_that_does_not_match_named_importer(self):
        spec = Mock()
        spec.name = "Fake"
        spec.matches_url.return_value = False

        with patch("apps.recipes.management.commands.recipe_importer.get_recipe_importers", return_value=[spec]):
            with self.assertRaises(CommandError):
                call_command("recipe_importer", "https://example.com/recipe", importer_name="Fake")

    def test_recipe_importer_rejects_ambiguous_auto_detection(self):
        first = Mock()
        first.name = "First"
        first.matches_url.return_value = True
        second = Mock()
        second.name = "Second"
        second.matches_url.return_value = True

        with patch("apps.recipes.management.commands.recipe_importer.get_recipe_importers", return_value=[first, second]):
            with self.assertRaises(CommandError):
                call_command("recipe_importer", "https://example.com/recipe")

    def test_recipe_importer_success_with_auto_detection(self):
        recipe = Recipe.objects.create(title="Cake")
        importer_cls = Mock()
        importer_cls.return_value.import_recipe.return_value = recipe
        spec = Mock()
        spec.name = "Fake"
        spec.matches_url.return_value = True
        spec.importer_cls = importer_cls
        output = StringIO()

        with patch("apps.recipes.management.commands.recipe_importer.get_recipe_importers", return_value=[spec]):
            call_command("recipe_importer", "https://example.com/recipe", stdout=output)

        importer_cls.assert_called_once_with(url="https://example.com/recipe")
        self.assertIn("Imported recipe 'Cake' via Fake.", output.getvalue())


class SeedCommandTests(TestCase):
    def test_seed_command_reports_success_and_handles_errors(self):
        class SuccessfulSeed(SeedCommand):
            def get_seed_name(self):
                return "Successful"

            def seed(self, *args, **kwargs):
                return None

        class FailingSeed(SeedCommand):
            def get_seed_name(self):
                return "Failing"

            def seed(self, *args, **kwargs):
                raise RuntimeError("boom")

        success = SuccessfulSeed()
        success.stdout = StringIO()
        success.handle()
        self.assertIn("Successfully seeded Successful.", success.stdout.getvalue())

        failing = FailingSeed()
        failing.stdout = StringIO()
        failing.handle()
        self.assertIn("Failed to seed Failing: boom", failing.stdout.getvalue())
        with self.assertRaises(RuntimeError):
            failing.handle(raise_on_error=True)

    def test_seed_admin_user_creates_or_updates_admin(self):
        SeedAdminUserCommand().seed()
        user = get_user_model().objects.get(username="admin")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("admin"))

    def test_seed_units_creates_catalog_units(self):
        SeedUnitsCommand().seed()

        self.assertTrue(Unit.objects.filter(name="gram", type="weight").exists())
        self.assertTrue(Unit.objects.filter(name="cup", type="volume").exists())

    def test_seed_ingredients_creates_catalog_ingredients(self):
        SeedIngredientsCommand().seed()

        self.assertTrue(Ingredient.objects.filter(name="milk", density=1.03).exists())
        self.assertTrue(Ingredient.objects.filter(name="flour", kcal=364).exists())

    def test_seed_all_reports_failed_seed_commands(self):
        success_command = Mock()
        success_command.return_value.handle.return_value = None
        failing_command = Mock()
        failing_command.__module__ = "apps.recipes.management.commands.failing_seed"
        failing_command.return_value.handle.side_effect = RuntimeError("boom")
        success_command.__module__ = "apps.recipes.management.commands.success_seed"
        output = StringIO()

        with patch.object(seed_all.Command, "SEED_COMMANDS", [success_command, failing_command]):
            call_command("seed_all", stdout=output)

        self.assertIn("OK success_seed succeeded", output.getvalue())
        self.assertIn("FAIL failing_seed failed: boom", output.getvalue())
        self.assertIn("WARN 1/2 seeds failed: failing_seed", output.getvalue())
