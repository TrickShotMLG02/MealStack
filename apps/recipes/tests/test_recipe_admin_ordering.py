from types import SimpleNamespace

from django.contrib import admin
from django.forms import HiddenInput
from django.test import RequestFactory, SimpleTestCase

from apps.recipes.admin.recipe import (
    RecipeComponentInline,
    RecipeImageInline,
    RecipeIngredientGroupInline,
    RecipeIngredientInline,
    RecipeNotesInline,
    RecipeStepGroupInline,
    RecipeStepInline,
)
from apps.recipes.models import (
    Recipe,
    RecipeComponent,
    RecipeImage,
    RecipeIngredientGroup,
    RecipeNote,
    RecipeStepGroup,
)


class RecipeAdminOrderingTests(SimpleTestCase):
    def test_ordered_recipe_inlines_enable_sorting_and_hide_order_fields(self):
        request = RequestFactory().get("/admin/recipes/recipe/1/change/")
        request.user = SimpleNamespace(has_perm=lambda _permission: True)
        ordered_inlines = (
            (RecipeIngredientGroupInline, Recipe, "order"),
            (RecipeIngredientInline, RecipeIngredientGroup, "order"),
            (RecipeStepGroupInline, Recipe, "order"),
            (RecipeStepInline, RecipeStepGroup, "order"),
            (RecipeComponentInline, Recipe, "order"),
            (RecipeNotesInline, Recipe, "ordering"),
            (RecipeImageInline, Recipe, "ordering"),
        )

        for inline_class, parent_model, order_field in ordered_inlines:
            with self.subTest(inline=inline_class.__name__):
                inline = inline_class(parent_model, admin.site)
                self.assertEqual(inline.sortable_field_name, order_field)
                self.assertFalse(inline.sortable_options["disabled"])

                formset = inline.get_formset(request)

                self.assertIsInstance(formset.form.base_fields[order_field].widget, HiddenInput)
