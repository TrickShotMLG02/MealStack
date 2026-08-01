from django.test import SimpleTestCase

from apps.recipes.management.commands.seed_catalog import (
    canonicalize_ingredient_name,
    ingredient_defaults,
    normalize_text,
    parse_ingredient_line,
    parse_quantity,
    should_start_new_step_group,
    unit_defaults,
)


class SeedCatalogParsingTests(SimpleTestCase):
    def test_normalize_text_replaces_unicode_fractions_and_spacing(self):
        self.assertEqual(normalize_text(" 1\u00bd\xa0cups \u2014 flour "), "1 1/2 cups - flour")

    def test_parse_quantity_supports_fractions_and_mixed_numbers(self):
        self.assertEqual(parse_quantity("1/2"), 0.5)
        self.assertEqual(parse_quantity("1 1/2"), 1.5)
        self.assertEqual(parse_quantity("1 0.5"), 1.5)
        self.assertEqual(parse_quantity("\u00be"), 0.75)

    def test_canonicalize_ingredient_name_uses_aliases_and_cleanup(self):
        cases = {
            "Large eggs": "egg",
            "self-raising flour": "flour",
            "sunflower or vegetable oil": "vegetable oil",
            "garlic cloves, chopped": "garlic",
            "tomatoes": "tomatoes",
            "lemon wedges to serve": "lemon",
            "parmesan cheese / breadcrumbs": "parmesan",
            "eggs (large)": "egg",
            "unknown things": "unknown things",
        }

        for raw_name, expected in cases.items():
            with self.subTest(raw_name=raw_name):
                self.assertEqual(canonicalize_ingredient_name(raw_name), expected)

    def test_parse_ingredient_line_supports_common_scraped_formats(self):
        cases = [
            ("100g flour", (100.0, "gram", "flour")),
            ("2 cups milk", (2.0, "cup", "milk")),
            ("1 1/2 tbsp olive oil", (1.5, "tbsp", "olive oil")),
            ("N/A salt", (1.0, "pcs", "salt")),
            ("1-oz can crushed tomatoes", (1.0, "oz", "tomatoes")),
            ("2 pcs 14 oz diced tomatoes", (14.0, "oz", "tomatoes")),
            ("large egg", (1.0, "pcs", "egg")),
            ("3kg chicken breasts, diced", (3.0, "kilogram", "chicken")),
            ("4 lb. chicken thighs plus sauce", (4.0, "lb", "chicken")),
            ("1 container ricotta cheese", (1.0, "pcs", "ricotta cheese")),
        ]

        for raw_line, expected in cases:
            with self.subTest(raw_line=raw_line):
                self.assertEqual(parse_ingredient_line(raw_line), expected)

    def test_step_group_detection_uses_short_heading_like_steps(self):
        self.assertTrue(should_start_new_step_group("For the sauce"))
        self.assertFalse(should_start_new_step_group(""))
        self.assertFalse(should_start_new_step_group("Mix everything together until smooth."))
        self.assertFalse(should_start_new_step_group("this is lowercase"))
        self.assertFalse(should_start_new_step_group("Bake!"))

    def test_catalog_default_helpers_return_known_values_and_empty_fallbacks(self):
        self.assertEqual(unit_defaults("gram")["type"], "weight")
        self.assertEqual(unit_defaults("missing"), {})
        self.assertEqual(ingredient_defaults("milk")["density"], 1.03)
        self.assertEqual(ingredient_defaults("missing"), {})
