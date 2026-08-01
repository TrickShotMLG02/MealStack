from unittest.mock import Mock, patch

from django.test import TestCase

from apps.recipes.importers.ingredients.base import EANNotFound, IngredientImporterError
from apps.recipes.importers.ingredients.openfoodfacts import OpenFoodFactsImporter
from apps.recipes.models import Ingredient


class IngredientImporterTests(TestCase):
    def test_openfoodfacts_importer_creates_ingredient_from_api_response(self):
        api = Mock()
        api.product.get.return_value = {
            "code": "1234567890123",
            "brands": "Acme, Other",
            "product_name": "Milk",
            "product_name_de": "Milch",
            "generic_name": "Milk generic",
            "generic_name_de": "Milch generisch",
            "nutriments": {
                "energy-kcal": 60,
                "fat_100g": 3.3,
                "saturated-fat_100g": 2.1,
                "carbohydrates_100g": 5,
                "sugars_100g": 4.8,
                "proteins_100g": 3.2,
                "salt_100g": 0.1,
            },
        }

        with patch("apps.recipes.importers.ingredients.openfoodfacts.openfoodfacts.API", return_value=api):
            ingredient = OpenFoodFactsImporter(ean="1234567890123").import_ingredient()

        self.assertEqual(ingredient.ean, "1234567890123")
        self.assertEqual(ingredient.name, "Milch")
        self.assertEqual(ingredient.generic_name, "Milch generisch")
        self.assertEqual(ingredient.brand, "Acme")
        self.assertEqual(ingredient.kcal, 60)
        self.assertEqual(Ingredient.objects.count(), 1)

    def test_openfoodfacts_importer_can_use_ean_argument(self):
        api = Mock()
        api.product.get.return_value = {
            "code": "999",
            "brands": "Brand",
            "product_name": "Sugar",
            "product_name_de": "",
            "generic_name": "Sweetener",
            "generic_name_de": "",
            "nutriments": {},
        }

        with patch("apps.recipes.importers.ingredients.openfoodfacts.openfoodfacts.API", return_value=api):
            ingredient = OpenFoodFactsImporter().import_ingredient("999")

        api.product.get.assert_called_once()
        self.assertEqual(ingredient.name, "Sugar")
        self.assertEqual(ingredient.kcal, 0)

    def test_openfoodfacts_importer_raises_for_missing_product(self):
        api = Mock()
        api.product.get.return_value = None

        with patch("apps.recipes.importers.ingredients.openfoodfacts.openfoodfacts.API", return_value=api):
            with self.assertRaises(EANNotFound) as context:
                OpenFoodFactsImporter(ean="missing").import_ingredient()

        self.assertEqual(context.exception.value, "missing")
        self.assertEqual(str(context.exception), "Product not found for EAN: missing")

    def test_ingredient_importer_error_uses_default_message(self):
        error = IngredientImporterError(value="x")

        self.assertEqual(error.value, "x")
        self.assertEqual(str(error), "Ingredient Importer error occurred")
