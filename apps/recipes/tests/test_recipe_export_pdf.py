from datetime import datetime, timedelta, timezone as datetime_timezone
from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.recipes.models import (
    Ingredient,
    Recipe,
    RecipeComponent,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeNote,
    RecipeStep,
    RecipeStepGroup,
    Unit,
)
from apps.recipes.services.pdf import _format_exported_at, _localized_text, build_recipe_pdf, recipe_pdf_filename
from apps.recipes.services.servings import coerce_servings, scale_nutrition, scale_quantity


class RecipeExportPdfTests(TestCase):
    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_export_timestamp_uses_website_language_and_browser_offset(self):
        exported_at = datetime(2026, 10, 15, 12, 34, tzinfo=datetime_timezone.utc)

        result = _format_exported_at(
            exported_at,
            timezone_name="Europe/Paris",
            timezone_offset="120",
            language_code="de",
        )

        self.assertIn("14:34", result)
        self.assertNotIn("12:34", result)

    def test_export_timestamp_falls_back_to_valid_zone_when_offset_is_invalid(self):
        exported_at = datetime(2026, 10, 15, 12, 34, tzinfo=datetime_timezone.utc)

        result = _format_exported_at(
            exported_at,
            timezone_name="Europe/Paris",
            timezone_offset="not-an-offset",
            language_code="de",
        )

        self.assertIn("14:34", result)

    def test_pdf_footer_labels_follow_website_language(self):
        from django.utils.translation import override

        with override("en"):
            exported_label = _localized_text("Exported at", "de")
            recipe_url_label = _localized_text("Recipe URL", "de")

        self.assertEqual(exported_label, "Exportiert um")
        self.assertEqual(recipe_url_label, "Rezept-URL")

    def test_export_view_canonicalizes_servings_url_and_passes_localization(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="published")
        export_url = reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug})

        with patch("apps.recipes.views.recipe_detail_view.build_recipe_pdf", return_value=b"%PDF") as build_pdf:
            response = self.client.get(
                export_url,
                {
                    "servings": "1.0",
                    "timezone": "Europe/Paris",
                    "timezone_offset": "120",
                },
                HTTP_ACCEPT_LANGUAGE="de",
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(build_pdf.call_args.args[1].endswith("?servings=1"))
        self.assertEqual(build_pdf.call_args.kwargs["timezone_name"], "Europe/Paris")
        self.assertEqual(build_pdf.call_args.kwargs["timezone_offset"], "120")
        self.assertEqual(build_pdf.call_args.kwargs["language_code"], "de")

        with patch("apps.recipes.views.recipe_detail_view.build_recipe_pdf", return_value=b"%PDF") as build_pdf:
            self.client.get(export_url, {"servings": "1.25"})

        self.assertTrue(build_pdf.call_args.args[1].endswith("?servings=1.25"))

    def test_pdf_story_includes_component_notes_and_rest_metric(self):
        parent = Recipe.objects.create(title="Meal", servings=2, status="published")
        child = Recipe.objects.create(
            title="Sauce",
            servings=2,
            status="published",
            resting_time=timedelta(minutes=8),
        )
        RecipeComponent.objects.create(parent_recipe=parent, child_recipe=child, servings=1)
        RecipeNote.objects.create(recipe=child, content="Season to taste.")
        captured = {}

        def capture_build(_document, story, **_kwargs):
            captured["story"] = story

        with patch("apps.recipes.services.pdf.SimpleDocTemplate.build", autospec=True, side_effect=capture_build):
            build_recipe_pdf(parent, "https://example.test/meal/?servings=2")

        def paragraphs(flowable):
            from reportlab.platypus import Paragraph, Table

            if isinstance(flowable, Paragraph):
                yield flowable.getPlainText()
            elif isinstance(flowable, Table):
                for row in flowable._cellvalues:
                    for cell in row:
                        if isinstance(cell, (list, tuple)):
                            for nested in cell:
                                yield from paragraphs(nested)
                        elif hasattr(cell, "wrap"):
                            yield from paragraphs(cell)

        story_text = " ".join(text for item in captured["story"] for text in paragraphs(item))
        self.assertIn("Rest", story_text)
        self.assertIn("8m", story_text)
        self.assertIn("Sauce: Season to taste.", story_text)

    def test_export_pdf_returns_pdf_response(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="published")
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
        self.assertIn('filename="cake.pdf"', response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_pdf_filename_uses_recipe_title_and_removes_forbidden_characters(self):
        self.assertEqual(
            recipe_pdf_filename('Mom\'s <best> cake: "really"?'),
            "moms-best-cake-really.pdf",
        )

    def test_pdf_filename_uses_recipe_slug_and_falls_back_for_empty_titles(self):
        self.assertEqual(recipe_pdf_filename("  Cake.  "), "cake.pdf")
        self.assertEqual(recipe_pdf_filename(""), "recipe.pdf")

    def test_export_pdf_uses_safe_recipe_title_as_filename(self):
        recipe = Recipe.objects.create(title="Fish & Chips: Mum's way?", servings=4, status="published")

        response = self.client.get(reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug}))

        self.assertEqual(
            response["Content-Disposition"],
            'inline; filename="fish-chips-mums-way.pdf"',
        )

    def test_export_pdf_accepts_servings_query_param(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="published")
        response = self.client.get(
            reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug}),
            {"servings": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_recipe_detail_accepts_mixed_fraction_servings(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="published")

        response = self.client.get(
            reverse("recipes:recipe_detail", kwargs={"slug": recipe.slug}),
            {"servings": "7 3/4"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_servings"], 7.75)

    def test_export_pdf_does_not_expose_drafts(self):
        recipe = Recipe.objects.create(title="Private Cake", servings=4, status="draft")

        response = self.client.get(reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug}))

        self.assertEqual(response.status_code, 404)

    @override_settings(PUBLIC_PDF_RATE_LIMIT=1, PUBLIC_RATE_LIMIT_WINDOW=60)
    def test_pdf_exports_are_rate_limited_per_client(self):
        recipe = Recipe.objects.create(title="Cake", servings=4, status="published")
        url = reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug})

        first = self.client.get(url)
        second = self.client.get(url)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second["Retry-After"], "60")

    def test_recipe_detail_does_not_expose_drafts(self):
        recipe = Recipe.objects.create(title="Private Cake", servings=4, status="draft")

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": recipe.slug}))

        self.assertEqual(response.status_code, 404)

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
        self.assertEqual(coerce_servings("2,5", 4), 2.5)
        self.assertAlmostEqual(coerce_servings("1/3", 4), 1 / 3)
        self.assertEqual(coerce_servings("1 1/2", 4), 1.5)
        self.assertEqual(coerce_servings("7 3/4", 4), 7.75)
        self.assertEqual(coerce_servings("7,5 1/2", 4), 8)
        self.assertEqual(coerce_servings("  7 3/4  ", 4), 7.75)
        self.assertEqual(coerce_servings("3/0", 4), 4)
        self.assertEqual(coerce_servings("7 3/0", 4), 4)
        self.assertEqual(coerce_servings("7 3", 4), 4)
        self.assertEqual(coerce_servings("-1", 4), 4)
        self.assertEqual(coerce_servings("0", 4), 4)
        self.assertEqual(scale_quantity(250, 4, 2), 125)
        self.assertEqual(scale_quantity(250, 4, 2.5), 156.25)

        totals = scale_nutrition(nutrition, 2.5)
        self.assertEqual(totals.kcal, 250)
        self.assertEqual(totals.protein, 25)
        self.assertEqual(totals.carbs, 50)
