import re
from datetime import timedelta

from django.db import transaction
from recipe_scrapers import scrape_me

from apps.recipes.importers.recipes.base import BaseRecipeImporter
from apps.recipes.management.commands.SeedCommand import SeedCommand
from apps.recipes.management.commands.seed_catalog import (
    RECIPE_FIXTURES,
    canonicalize_ingredient_name,
    ingredient_defaults,
    parse_ingredient_line,
    should_start_new_step_group,
)
from apps.recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeNutrition,
    RecipeStep,
    RecipeStepGroup,
    Tag,
    Unit,
)
from apps.recipes.services.nutrition import update_recipe_nutrition


class Command(SeedCommand):
    help = "Seed demo recipes from English recipe pages"

    def get_seed_name(self):
        return "Recipes"

    def _ensure_unit(self, name: str) -> Unit:
        from apps.recipes.management.commands.seed_catalog import unit_defaults

        unit, _ = Unit.objects.update_or_create(
            name=name,
            defaults=unit_defaults(name),
        )
        return unit

    def _ensure_ingredient(self, name: str) -> Ingredient:
        canonical_name = canonicalize_ingredient_name(name)
        defaults = ingredient_defaults(canonical_name)
        ingredient, _ = Ingredient.objects.update_or_create(
            slug=re.sub(r"[^a-z0-9-]+", "-", canonical_name.lower()).strip("-"),
            defaults={
                "name": canonical_name,
                **defaults,
            },
        )
        return ingredient

    def _clear_recipe_payload(self, recipe: Recipe) -> None:
        recipe.tags.clear()
        recipe.recipeimage_set.all().delete()
        recipe.recipeingredientgroup_set.all().delete()
        recipe.recipestepgroup_set.all().delete()
        RecipeNutrition.objects.filter(recipe=recipe).delete()

    def _parse_servings(self, raw_yields: str | None, fallback: int = 1) -> int:
        if not raw_yields:
            return fallback
        match = re.search(r"\d+", raw_yields)
        return int(match.group()) if match else fallback

    def _safe_minutes(self, scraper, attr_name: str) -> int:
        try:
            value = getattr(scraper, attr_name)()
        except Exception:
            return 0

        if not value:
            return 0

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _safe_text(self, scraper, attr_name: str) -> str:
        try:
            value = getattr(scraper, attr_name)()
        except Exception:
            return ""
        return (value or "") if isinstance(value, str) else str(value or "")

    def _create_ingredients(self, recipe: Recipe, scraper) -> None:
        try:
            ingredient_groups = scraper.ingredient_groups()
        except Exception:
            ingredient_groups = []

        if ingredient_groups:
            for group_order, scraped_group in enumerate(ingredient_groups):
                group_name = (scraped_group.purpose or "").strip() or f"Group {group_order + 1}"
                group = RecipeIngredientGroup.objects.create(recipe=recipe, name=group_name, order=group_order)
                for ingredient_order, raw_line in enumerate(scraped_group.ingredients):
                    self._create_recipe_ingredient(recipe, group, raw_line, ingredient_order)
            return

        group = RecipeIngredientGroup.objects.create(recipe=recipe, name="Main", order=0)
        for ingredient_order, raw_line in enumerate(scraper.ingredients()):
            self._create_recipe_ingredient(recipe, group, raw_line, ingredient_order)

    def _create_recipe_ingredient(self, recipe: Recipe, group: RecipeIngredientGroup, raw_line: str, order: int) -> None:
        quantity, unit_name, ingredient_name = parse_ingredient_line(raw_line)
        unit = self._ensure_unit(unit_name)
        ingredient = self._ensure_ingredient(ingredient_name)
        RecipeIngredient.objects.create(
            ingredient=ingredient,
            quantity=quantity,
            unit=unit,
            group=group,
            order=order,
        )

    def _create_steps(self, recipe: Recipe, scraper) -> None:
        instructions = [step.strip() for step in scraper.instructions_list() if step and step.strip()]
        current_group = RecipeStepGroup.objects.create(recipe=recipe, name="Method", order=0)
        group_order = 0
        step_order = 0

        for raw_step in instructions:
            if should_start_new_step_group(raw_step):
                if step_order == 0 and group_order == 0 and current_group.name == "Method":
                    current_group.name = raw_step.strip()
                    current_group.save(update_fields=["name"])
                else:
                    group_order += 1
                    current_group = RecipeStepGroup.objects.create(recipe=recipe, name=raw_step.strip(), order=group_order)
                    step_order = 0
                continue

            step_order += 1
            RecipeStep.objects.create(
                group=current_group,
                order=step_order,
                description=raw_step,
            )

    @transaction.atomic
    def _seed_single_recipe(self, fixture: dict) -> Recipe:
        scraper = scrape_me(fixture["url"])
        title = self._safe_text(scraper, "title").strip()[:250]
        recipe, _ = Recipe.objects.update_or_create(
            source=fixture["url"],
            defaults={
                "title": title,
                "servings": self._parse_servings(scraper.yields(), fallback=1),
                "preparation_time": timedelta(minutes=self._safe_minutes(scraper, "prep_time")),
                "cooking_time": timedelta(minutes=self._safe_minutes(scraper, "cook_time")),
                "resting_time": timedelta(0),
                "status": "published",
                "author": self._safe_text(scraper, "author")[:40],
            },
        )

        self._clear_recipe_payload(recipe)

        for tag_name in fixture["tags"]:
            tag, _ = Tag.objects.update_or_create(name=tag_name, defaults={})
            recipe.tags.add(tag)

        self._create_ingredients(recipe, scraper)
        self._create_steps(recipe, scraper)

        image_url = scraper.image()
        if image_url:
            try:
                BaseRecipeImporter.attach_image(recipe, image_url, primary=True, ordering=0)
            except Exception:
                pass

        update_recipe_nutrition(recipe)
        return recipe

    def seed(self, *args, **kwargs):
        for fixture in RECIPE_FIXTURES:
            self._seed_single_recipe(fixture)
