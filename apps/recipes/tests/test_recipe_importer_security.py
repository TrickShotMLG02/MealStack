from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.recipes.importers.recipes.base import BaseRecipeImporter, RecipeImageImportError
from apps.recipes.importers.recipes.registry import get_recipe_importers


class RecipeImporterSecurityTests(SimpleTestCase):
    def test_registered_recipe_importers_define_base_domains(self):
        importer_domains = {importer.name: importer.base_domain for importer in get_recipe_importers()}

        self.assertEqual(importer_domains["BBC Good Food"], "bbcgoodfood.com")
        self.assertEqual(importer_domains["Chefkoch"], "chefkoch.de")
        self.assertEqual(importer_domains["Epicurious"], "epicurious.com")

    def test_attach_image_rejects_url_outside_importer_domain(self):
        with self.assertRaises(RecipeImageImportError):
            BaseRecipeImporter.attach_image(
                recipe=object(),
                image_url="https://example.com/image.jpg",
                base_domain="bbcgoodfood.com",
            )

    def test_attach_image_rejects_non_image_content_type(self):
        response = SimpleNamespace(
            url="https://www.bbcgoodfood.com/image.jpg",
            headers={"Content-Type": "text/html; charset=utf-8"},
            content=b"<html></html>",
            raise_for_status=lambda: None,
        )

        with patch("apps.recipes.importers.recipes.base.requests.get", return_value=response):
            with self.assertRaises(RecipeImageImportError):
                BaseRecipeImporter.attach_image(
                    recipe=object(),
                    image_url="https://www.bbcgoodfood.com/image.jpg",
                    base_domain="bbcgoodfood.com",
                )

    def test_attach_image_rejects_redirect_outside_importer_domain(self):
        response = SimpleNamespace(
            url="https://example.com/image.jpg",
            headers={"Content-Type": "image/jpeg"},
            content=b"image",
            raise_for_status=lambda: None,
        )

        with patch("apps.recipes.importers.recipes.base.requests.get", return_value=response):
            with self.assertRaises(RecipeImageImportError):
                BaseRecipeImporter.attach_image(
                    recipe=object(),
                    image_url="https://www.bbcgoodfood.com/image.jpg",
                    base_domain="bbcgoodfood.com",
                )
