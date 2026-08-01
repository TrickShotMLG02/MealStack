from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.recipes.importers.ingredients.base import EANNotFound
from apps.recipes.views import admin_importers_view


class AdminImporterViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _render_context(self, view, request):
        with patch("apps.recipes.views.admin_importers_view.render") as render:
            render.side_effect = lambda _request, template, context: SimpleNamespace(
                template=template,
                context=context,
            )
            return view(request)

    def test_ingredient_importer_get_renders_without_message(self):
        response = self._render_context(
            admin_importers_view.ingredient_importer,
            self.factory.get("/admin/importers/ingredient/openfoodfacts/"),
        )

        self.assertEqual(response.template, "admin/ingredient_importer.html")
        self.assertIsNone(response.context["message"])

    def test_ingredient_importer_requires_ean(self):
        response = self._render_context(
            admin_importers_view.ingredient_importer,
            self.factory.post("/admin/importers/ingredient/openfoodfacts/", data={}),
        )

        self.assertEqual(response.context["message"], "Please provide a valid EAN.")

    @patch("apps.recipes.views.admin_importers_view.OpenFoodFactsImporter")
    def test_ingredient_importer_success(self, importer_cls):
        importer_cls.return_value.import_ingredient.return_value = SimpleNamespace(name="Milk")

        response = self._render_context(
            admin_importers_view.ingredient_importer,
            self.factory.post("/admin/importers/ingredient/openfoodfacts/", data={"ean": "123"}),
        )

        self.assertEqual(response.context["message"], "Ingredient 'Milk' imported successfully!")

    @patch("apps.recipes.views.admin_importers_view.OpenFoodFactsImporter")
    def test_ingredient_importer_handles_missing_ean_and_generic_errors(self, importer_cls):
        importer_cls.return_value.import_ingredient.side_effect = EANNotFound("123")
        response = self._render_context(
            admin_importers_view.ingredient_importer,
            self.factory.post("/admin/importers/ingredient/openfoodfacts/", data={"ean": "123"}),
        )
        self.assertEqual(response.context["message"], "EAN 123 not found in OpenFoodFacts.")

        importer_cls.return_value.import_ingredient.side_effect = RuntimeError("offline")
        response = self._render_context(
            admin_importers_view.ingredient_importer,
            self.factory.post("/admin/importers/ingredient/openfoodfacts/", data={"ean": "123"}),
        )
        self.assertEqual(response.context["message"], "Error: offline")

    def test_recipe_importer_view_get_and_validation_messages(self):
        importer_spec = Mock()
        importer_spec.name = "Fake"
        importer_spec.url_placeholder = "https://example.com/recipe"
        importer_spec.matches_url.return_value = False

        response = self._render_context(
            admin_importers_view.make_recipe_importer_view(importer_spec),
            self.factory.get("/admin/importers/recipe/fake/"),
        )
        self.assertEqual(response.template, "admin/recipe_importer.html")
        self.assertEqual(response.context["site_name"], "Fake")
        self.assertIsNone(response.context["message"])

        response = self._render_context(
            admin_importers_view.make_recipe_importer_view(importer_spec),
            self.factory.post("/admin/importers/recipe/fake/", data={}),
        )
        self.assertEqual(response.context["message"], "Please provide a valid recipe URL.")

        response = self._render_context(
            admin_importers_view.make_recipe_importer_view(importer_spec),
            self.factory.post("/admin/importers/recipe/fake/", data={"url": "https://other.test/"}),
        )
        self.assertEqual(
            response.context["message"],
            "Invalid URL for Fake. Please use a matching recipe URL.",
        )

    def test_recipe_importer_view_success_and_error(self):
        importer_cls = Mock()
        importer_cls.return_value.import_recipe.return_value = SimpleNamespace(title="Cake")
        importer_spec = Mock()
        importer_spec.name = "Fake"
        importer_spec.url_placeholder = "https://example.com/recipe"
        importer_spec.matches_url.return_value = True
        importer_spec.importer_cls = importer_cls
        view = admin_importers_view.make_recipe_importer_view(importer_spec)

        response = self._render_context(
            view,
            self.factory.post("/admin/importers/recipe/fake/", data={"url": "https://example.com/recipe"}),
        )
        self.assertEqual(response.context["message"], "Recipe 'Cake' imported successfully!")

        importer_cls.return_value.import_recipe.side_effect = RuntimeError("offline")
        response = self._render_context(
            view,
            self.factory.post("/admin/importers/recipe/fake/", data={"url": "https://example.com/recipe"}),
        )
        self.assertEqual(response.context["message"], "Error importing recipe: offline")

    def test_importer_home_views_build_expected_context(self):
        home = self._render_context(
            admin_importers_view.importers_home,
            self.factory.get("/admin/importers/"),
        )
        self.assertEqual(home.context["section_title"], "Importers")
        self.assertEqual(len(home.context["importers"]), 2)

        ingredients_home = self._render_context(
            admin_importers_view.ingredient_importers_home,
            self.factory.get("/admin/importers/ingredient/"),
        )
        self.assertEqual(ingredients_home.context["importers"][0]["name"], "OpenFoodFacts")

        recipe_spec = Mock()
        recipe_spec.name = "Fake"
        recipe_spec.url_path = "recipe/fake/"
        with patch("apps.recipes.views.admin_importers_view.get_recipe_importers", return_value=[recipe_spec]):
            recipes_home = self._render_context(
                admin_importers_view.recipe_importers_home,
                self.factory.get("/admin/importers/recipe/"),
            )

        self.assertEqual(recipes_home.context["section_title"], "Recipe Scrapers")
        self.assertEqual(recipes_home.context["importers"][0]["url"], "/admin/importers/recipe/fake/")
