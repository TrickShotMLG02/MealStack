from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override
from django.contrib import admin

from apps.recipes.models import (
    Ingredient,
    Recipe,
    RecipeComponent,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeNutrition,
    RecipeStep,
    RecipeStepGroup,
    Unit,
)
from apps.recipes.services.composition import CompositionError, compose_recipe
from apps.recipes.services.nutrition import update_recipe_nutrition
from apps.recipes.admin.recipe import RecipeAdmin


class RecipeCompositionTests(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(name="gram", type="weight", grams_per_unit=1)
        self.sugar = Ingredient.objects.create(
            name="Sugar",
            kcal=400,
            carbs=100,
            sugar=100,
            protein=0,
            fat=0,
            saturates=0,
            salt=0,
        )
        self.flour = Ingredient.objects.create(
            name="Flour",
            kcal=350,
            carbs=70,
            sugar=2,
            protein=10,
            fat=2,
            saturates=0.5,
            salt=0.1,
        )

    def make_recipe(self, title, servings=4, status="published", visibility="listed", quantity=None, ingredient=None, step=None):
        recipe = Recipe.objects.create(
            title=title,
            servings=servings,
            status=status,
            visibility=visibility,
            preparation_time=timedelta(minutes=5),
            cooking_time=timedelta(minutes=10),
            resting_time=timedelta(minutes=2),
        )
        if quantity is not None:
            group = RecipeIngredientGroup.objects.create(recipe=recipe, name="Main", order=0)
            RecipeIngredient.objects.create(
                group=group,
                ingredient=ingredient or self.sugar,
                quantity=quantity,
                unit=self.unit,
                order=0,
            )
        if step:
            step_group = RecipeStepGroup.objects.create(recipe=recipe, name="Method", order=0)
            RecipeStep.objects.create(group=step_group, description=step, order=0)
        update_recipe_nutrition(recipe)
        return recipe

    def test_composition_scales_parent_and_linked_recipe_ingredients(self):
        sauce = self.make_recipe("Tomato sauce", servings=2, quantity=200, step="Simmer the sauce.")
        pasta = self.make_recipe("Pasta", servings=4, quantity=400, step="Boil the pasta.")
        RecipeComponent.objects.create(parent_recipe=pasta, child_recipe=sauce, servings=2, order=0)

        composition = compose_recipe(pasta, require_published=True)

        self.assertEqual([section.title for section in composition.sections], ["Pasta", "Tomato sauce"])
        self.assertEqual(composition.sections[0].ingredient_groups[0].ingredients[0].quantity, 400)
        self.assertEqual(composition.sections[1].ingredient_groups[0].ingredients[0].quantity, 200)
        self.assertEqual(composition.sections[1].step_groups[0].steps[0].description, "Simmer the sauce.")

    def test_nested_components_are_expanded_and_scaled_recursively(self):
        spice = self.make_recipe("Spice mix", servings=8, quantity=80, step="Mix spices.")
        sauce = self.make_recipe("Sauce", servings=4, quantity=200, step="Cook sauce.")
        RecipeComponent.objects.create(parent_recipe=sauce, child_recipe=spice, servings=2, order=0)
        meal = self.make_recipe("Meal", servings=4, quantity=400, step="Assemble meal.")
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2, order=0)

        composition = compose_recipe(meal, require_published=True)

        self.assertEqual([section.title for section in composition.sections], ["Meal", "Sauce", "Spice mix"])
        # Two sauce servings are half the sauce recipe; the sauce uses two of
        # eight spice servings, resulting in one spice serving in the meal.
        self.assertEqual(composition.sections[2].ingredient_groups[0].ingredients[0].quantity, 10)

    def test_nutrition_combines_components_and_scales_to_root_servings(self):
        sauce = self.make_recipe("Sauce", servings=2, quantity=200)
        meal = self.make_recipe("Meal", servings=4, quantity=400)
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        composition = compose_recipe(meal, require_published=True)

        # Meal: 400 g sugar = 1600 kcal; sauce: 200 g = 800 kcal; total 2400.
        self.assertEqual(composition.nutrition.total_kcal, 2400)
        self.assertEqual(composition.nutrition.per_serving_kcal, 600)
        self.assertEqual(composition.nutrition.per_serving_carbs, 150)

    def test_child_nutrition_updates_are_reflected_without_recalculating_parent(self):
        sauce = self.make_recipe("Sauce", servings=2, quantity=200)
        meal = self.make_recipe("Meal", servings=4, quantity=400)
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        before = compose_recipe(meal, require_published=True).nutrition.total_kcal
        sauce_ingredient = sauce.recipeingredientgroup_set.get().recipeingredient_set.get()
        sauce_ingredient.quantity = 300
        sauce_ingredient.save()
        update_recipe_nutrition(sauce)
        after = compose_recipe(meal, require_published=True).nutrition.total_kcal

        self.assertEqual(before, 2400)
        self.assertEqual(after, 2800)
        self.assertTrue(RecipeNutrition.objects.filter(recipe=meal).exists())

    def test_parallel_time_uses_the_slowest_track(self):
        sauce = self.make_recipe("Sauce", servings=2)
        sauce.preparation_time = timedelta(minutes=20)
        sauce.cooking_time = timedelta(minutes=40)
        sauce.resting_time = timedelta(minutes=1)
        sauce.save()
        meal = self.make_recipe("Meal", servings=4)
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        composition = compose_recipe(meal, require_published=True)

        self.assertEqual(composition.preparation_time, timedelta(minutes=20))
        self.assertEqual(composition.cooking_time, timedelta(minutes=40))
        self.assertEqual(composition.resting_time, timedelta(minutes=2))
        self.assertEqual(composition.total_time, timedelta(minutes=62))

    def test_public_detail_renders_all_component_sections_and_aggregate_nutrition(self):
        sauce = self.make_recipe("Tomato sauce", servings=2, quantity=200, step="Simmer the sauce.")
        meal = self.make_recipe("Pasta dinner", servings=4, quantity=400, step="Boil the pasta.")
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": meal.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tomato sauce")
        self.assertContains(response, "Simmer the sauce.")
        self.assertContains(response, 'data-per-serving="600.0"')
        self.assertContains(response, 'data-base-quantity="200.0"')
        self.assertContains(response, "href=\"/recipes/tomato-sauce/\"")

    def test_published_parent_hides_if_component_is_unpublished(self):
        sauce = self.make_recipe("Draft sauce", status="draft", quantity=200)
        meal = self.make_recipe("Meal", quantity=400)
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": meal.slug}))

        self.assertEqual(response.status_code, 404)

    def test_public_pdf_renders_composed_recipe_with_requested_servings(self):
        sauce = self.make_recipe("Tomato sauce", servings=2, quantity=200, step="Simmer the sauce.")
        meal = self.make_recipe("Pasta dinner", servings=4, quantity=400, step="Boil the pasta.")
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        response = self.client.get(
            reverse("recipes:recipe_export_pdf", kwargs={"slug": meal.slug}),
            {"servings": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_public_pdf_rejects_unpublished_component(self):
        sauce = self.make_recipe("Draft sauce", status="draft", quantity=200)
        meal = self.make_recipe("Meal", quantity=400)
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        response = self.client.get(reverse("recipes:recipe_export_pdf", kwargs={"slug": meal.slug}))

        self.assertEqual(response.status_code, 404)

    def test_component_only_recipe_is_embedded_but_not_linked_as_a_standalone_page(self):
        topping = self.make_recipe("Private topping", visibility="component_only", quantity=100, step="Add topping.")
        meal = self.make_recipe("Public meal", quantity=400, step="Prepare meal.")
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=topping, servings=1)

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": meal.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Private topping")
        self.assertContains(response, "Add topping.")
        self.assertNotContains(response, f'href="/recipes/{topping.slug}/"')

    def test_component_only_recipe_cannot_be_viewed_or_exported_directly(self):
        recipe = self.make_recipe("Private topping", visibility="component_only")

        detail = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": recipe.slug}))
        pdf = self.client.get(reverse("recipes:recipe_export_pdf", kwargs={"slug": recipe.slug}))

        self.assertEqual(detail.status_code, 404)
        self.assertEqual(pdf.status_code, 404)

    def test_empty_parent_and_component_sections_are_hidden_when_other_ingredients_exist(self):
        empty_parent = self.make_recipe("Pizza Neapolitana")
        empty_component = self.make_recipe("Empty component")
        dough = self.make_recipe("Dough", quantity=100)
        topping_group = RecipeIngredientGroup.objects.create(recipe=dough, name="Empty group", order=1)
        RecipeComponent.objects.create(parent_recipe=empty_parent, child_recipe=empty_component, servings=1)
        RecipeComponent.objects.create(parent_recipe=empty_parent, child_recipe=dough, servings=1)

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": empty_parent.slug}))
        ingredient_panel = response.content.decode().split('id="ingredients-panel"', 1)[1].split(
            'id="steps-panel"', 1
        )[0]

        self.assertNotIn("Pizza Neapolitana", ingredient_panel)
        self.assertNotIn("Empty component", ingredient_panel)
        self.assertIn("Dough", ingredient_panel)
        self.assertNotIn("No ingredients added yet.", response.content.decode())
        self.assertFalse(
            any(group.name == topping_group.name for group in compose_recipe(empty_parent).sections[-1].ingredient_groups)
        )

    def test_empty_parent_and_component_step_sections_are_hidden_when_other_steps_exist(self):
        empty_parent = self.make_recipe("Pizza Neapolitana")
        empty_component = self.make_recipe("Empty component")
        method_recipe = self.make_recipe("Dough", step="Knead the dough.")
        empty_step_group = RecipeStepGroup.objects.create(recipe=method_recipe, name="Empty method", order=1)
        RecipeComponent.objects.create(parent_recipe=empty_parent, child_recipe=empty_component, servings=1)
        RecipeComponent.objects.create(parent_recipe=empty_parent, child_recipe=method_recipe, servings=1)

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": empty_parent.slug}))
        step_panel = response.content.decode().split('id="steps-panel"', 1)[1].split(
            '</section>', 1
        )[0]
        composition = compose_recipe(empty_parent)

        self.assertTrue(composition.has_steps)
        self.assertNotIn("Pizza Neapolitana", step_panel)
        self.assertNotIn("Empty component", step_panel)
        self.assertIn("Dough", step_panel)
        self.assertIn("Knead the dough.", step_panel)
        self.assertNotIn("No steps added yet.", response.content.decode())
        self.assertFalse(
            any(group.name == empty_step_group.name for group in composition.sections[-1].step_groups)
        )

    def test_recipe_component_plural_is_localized_in_german(self):
        with override("de"):
            self.assertEqual(str(RecipeComponent._meta.verbose_name_plural), "Rezeptkomponenten")

    def test_child_can_supply_the_only_available_nutrition(self):
        sauce = self.make_recipe("Sauce", servings=2, quantity=200)
        meal = Recipe.objects.create(title="Meal", servings=4, status="published")
        RecipeComponent.objects.create(parent_recipe=meal, child_recipe=sauce, servings=2)

        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": meal.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-per-serving="200.0"')

    def test_composition_without_any_nutrition_is_still_renderable(self):
        recipe = Recipe.objects.create(title="Empty recipe", servings=2, status="published")

        composition = compose_recipe(recipe, require_published=True)
        response = self.client.get(reverse("recipes:recipe_detail", kwargs={"slug": recipe.slug}))

        self.assertIsNone(composition.nutrition)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "nutrition-summary-title")

    def test_maximum_depth_is_enforced(self):
        root = self.make_recipe("Root")
        child = self.make_recipe("Child")
        grandchild = self.make_recipe("Grandchild")
        RecipeComponent.objects.create(parent_recipe=root, child_recipe=child, servings=1)
        RecipeComponent.objects.create(parent_recipe=child, child_recipe=grandchild, servings=1)

        with self.assertRaises(CompositionError):
            compose_recipe(root, max_depth=1)

    def test_self_link_and_cycle_are_rejected(self):
        first = self.make_recipe("First")
        second = self.make_recipe("Second")
        RecipeComponent.objects.create(parent_recipe=first, child_recipe=second, servings=1)

        self_link = RecipeComponent(parent_recipe=first, child_recipe=first, servings=1)
        with self.assertRaises(ValidationError):
            self_link.full_clean()

        cycle = RecipeComponent(parent_recipe=second, child_recipe=first, servings=1)
        with self.assertRaises(ValidationError):
            cycle.full_clean()

    def test_component_used_servings_must_be_positive(self):
        parent = self.make_recipe("Parent")
        child = self.make_recipe("Child")
        component = RecipeComponent(parent_recipe=parent, child_recipe=child, servings=0)

        with self.assertRaises(ValidationError):
            component.full_clean()

    def test_duplicate_component_relationship_is_protected_by_unique_constraint(self):
        parent = self.make_recipe("Parent")
        child = self.make_recipe("Child")
        RecipeComponent.objects.create(parent_recipe=parent, child_recipe=child, servings=1)

        with self.assertRaises(IntegrityError):
            RecipeComponent.objects.create(parent_recipe=parent, child_recipe=child, servings=1)

    def test_deleting_child_recipe_is_protected(self):
        parent = self.make_recipe("Parent")
        child = self.make_recipe("Child")
        RecipeComponent.objects.create(parent_recipe=parent, child_recipe=child, servings=1)

        with self.assertRaises(ProtectedError):
            child.delete()

    def test_deleting_parent_removes_link_but_keeps_child(self):
        parent = self.make_recipe("Parent")
        child = self.make_recipe("Child")
        component = RecipeComponent.objects.create(parent_recipe=parent, child_recipe=child, servings=1)

        parent.delete()

        self.assertTrue(Recipe.objects.filter(pk=child.pk).exists())
        self.assertFalse(RecipeComponent.objects.filter(pk=component.pk).exists())

    def test_title_override_is_used_for_component_section(self):
        child = self.make_recipe("Internal sauce", quantity=100)
        parent = self.make_recipe("Meal")
        RecipeComponent.objects.create(
            parent_recipe=parent,
            child_recipe=child,
            servings=1,
            title_override="Sauce",
        )

        composition = compose_recipe(parent)

        self.assertEqual(composition.sections[1].title, "Sauce")

    def test_admin_explains_live_impact_of_editing_a_shared_recipe(self):
        child = self.make_recipe("Shared sauce")
        parent = self.make_recipe("Pizza")
        RecipeComponent.objects.create(parent_recipe=parent, child_recipe=child, servings=1)
        recipe_admin = RecipeAdmin(Recipe, admin.site)

        notice = recipe_admin.component_usage_notice(child)

        self.assertIn("Pizza", str(notice))
        self.assertIn("nutrition", str(notice))
