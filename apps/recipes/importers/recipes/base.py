import re
from abc import ABC, abstractmethod
from datetime import timedelta

import requests
from django.core.files.base import ContentFile
from recipe_scrapers import scrape_me

from apps.common.text_formatting import slugify
from apps.recipes.management.commands.seed_catalog import (
    canonicalize_ingredient_name,
    ingredient_defaults,
    parse_ingredient_line,
    should_start_new_step_group,
    unit_defaults,
)
from apps.recipes.models import (
    Ingredient,
    Recipe,
    RecipeImage,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeNutrition,
    RecipeStep,
    RecipeStepGroup,
    Tag,
    Unit,
)
from apps.recipes.services.nutrition import update_recipe_nutrition

class BaseRecipeImporter(ABC):
    """
    Abstract base class for all recipe importers.
    """

    @abstractmethod
    def import_recipe(self) -> Recipe:
        """
        Import a recipe from the given URL and return the Recipe object.
        """
        pass

    @staticmethod
    def normalize_ingredient_name(name: str) -> str:
        """
        Normalize ingredient name for lookup:
        - Remove parentheses for plurals like Ei(er) or Egg(s)
        """
        name = name.strip()

        # Remove content inside parentheses
        name = re.sub(r"\(.*?\)", "", name).strip()

        return name

    @staticmethod
    def normalize_quantity(quantity: float, scraped_unit: str, ingredient_density: float | None = None):
        """
        Convert quantity to base units:
          - weight in grams
          - volume in ml
          - count stays as-is

        ingredient_density: grams per ml for volume->weight conversion
        """
        # TODO: Implement this

        raise NotImplementedError("Not yet implemented")

    @staticmethod
    def normalize_ingredient(text: str):
        """
        Simple helper to parse quantity/unit/ingredient from raw text.
        Can be overridden or extended per website.
        """
        parts = text.split()
        try:
            quantity = float(parts[0])
            unit = parts[1] if len(parts) > 2 else ""
            name = " ".join(parts[2:]) if len(parts) > 2 else parts[1]
        except ValueError:
            quantity = 1
            unit = ""
            name = text
        return quantity, unit, name

    @abstractmethod
    def to_json(self) -> str:
        """
        Return the JSON string representation of the object.
        :return: JSON string
        """
        pass

    @staticmethod
    def attach_image(recipe, image_url, *, primary=False, ordering=0):
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        filename = image_url.split("/")[-1].split("?")[0]

        RecipeImage.objects.create(
            recipe=recipe,
            image=ContentFile(response.content, name=filename),
            is_primary=primary,
            ordering=ordering,
        )


class BaseRecipeScraperImporter(BaseRecipeImporter, ABC):
    site_name = "Recipe"
    default_ingredient_group_name = "Main"
    default_step_group_name = "Method"
    url_placeholder = "https://example.com/recipe"

    def __init__(self, url: str):
        self.url = url
        self.scraper = scrape_me(url)

    def normalize_title(self, title: str) -> str:
        return title.strip()

    def _safe_text(self, attr_name: str) -> str:
        try:
            value = getattr(self.scraper, attr_name)()
        except Exception:
            return ""
        return (value or "") if isinstance(value, str) else str(value or "")

    def _safe_minutes(self, attr_name: str) -> int:
        try:
            value = getattr(self.scraper, attr_name)()
        except Exception:
            return 0

        if not value:
            return 0

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _parse_servings(self, raw_yields: str | None, fallback: int = 1) -> int:
        if not raw_yields:
            return fallback
        match = re.search(r"\d+", raw_yields)
        return int(match.group()) if match else fallback

    def _ensure_unit(self, name: str) -> Unit:
        unit_name = name or "pcs"
        unit, _ = Unit.objects.update_or_create(
            name=unit_name,
            defaults=unit_defaults(unit_name),
        )
        return unit

    def _ensure_ingredient(self, name: str) -> Ingredient:
        canonical_name = canonicalize_ingredient_name(name)
        ingredient, _ = Ingredient.objects.update_or_create(
            slug=re.sub(r"[^a-z0-9-]+", "-", canonical_name.lower()).strip("-"),
            defaults={
                "name": canonical_name,
                **ingredient_defaults(canonical_name),
            },
        )
        return ingredient

    def _clear_recipe_payload(self, recipe: Recipe) -> None:
        recipe.tags.clear()
        recipe.recipeimage_set.all().delete()
        recipe.recipeingredientgroup_set.all().delete()
        recipe.recipestepgroup_set.all().delete()
        RecipeNutrition.objects.filter(recipe=recipe).delete()

    def _create_ingredients(self, recipe: Recipe) -> None:
        try:
            ingredient_groups = self.scraper.ingredient_groups()
        except Exception:
            ingredient_groups = []

        if ingredient_groups:
            for group_order, scraped_group in enumerate(ingredient_groups):
                group_name = (scraped_group.purpose or "").strip() or f"{self.default_ingredient_group_name} {group_order + 1}"
                group = RecipeIngredientGroup.objects.create(recipe=recipe, name=group_name, order=group_order)
                for ingredient_order, raw_line in enumerate(scraped_group.ingredients):
                    self._create_recipe_ingredient(group, raw_line, ingredient_order)
            return

        group = RecipeIngredientGroup.objects.create(recipe=recipe, name=self.default_ingredient_group_name, order=0)
        for ingredient_order, raw_line in enumerate(self.scraper.ingredients()):
            self._create_recipe_ingredient(group, raw_line, ingredient_order)

    def _create_recipe_ingredient(self, group: RecipeIngredientGroup, raw_line: str, order: int) -> None:
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

    def _create_steps(self, recipe: Recipe) -> None:
        instructions = [step.strip() for step in self.scraper.instructions_list() if step and step.strip()]
        current_group = RecipeStepGroup.objects.create(recipe=recipe, name=self.default_step_group_name, order=0)
        group_order = 0
        step_order = 0

        for raw_step in instructions:
            if should_start_new_step_group(raw_step):
                if step_order == 0 and group_order == 0 and current_group.name == self.default_step_group_name:
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

    def _attach_image(self, recipe: Recipe) -> None:
        try:
            image_url = self.scraper.image()
        except Exception:
            image_url = ""

        if image_url:
            try:
                BaseRecipeImporter.attach_image(recipe, image_url, primary=True, ordering=0)
            except Exception:
                pass

    def import_recipe(self) -> Recipe:
        title = self.normalize_title(self._safe_text("title").strip())[:250] or self.site_name
        recipe, _ = Recipe.objects.update_or_create(
            source=self.url,
            defaults={
                "title": title,
                "servings": self._parse_servings(self.scraper.yields(), fallback=1),
                "preparation_time": timedelta(minutes=self._safe_minutes("prep_time")),
                "cooking_time": timedelta(minutes=self._safe_minutes("cook_time")),
                "resting_time": timedelta(0),
                "status": "published",
                "author": self._safe_text("author")[:40],
            },
        )

        self._clear_recipe_payload(recipe)
        self._create_ingredients(recipe)
        self._create_steps(recipe)

        for tag_name in getattr(self.scraper, "keywords", lambda: [])() or []:
            tag_name = str(tag_name).strip()
            if not tag_name:
                continue
            tag, _ = Tag.objects.update_or_create(
                slug=slugify(tag_name),
                defaults={"name": tag_name},
            )
            recipe.tags.add(tag)

        self._attach_image(recipe)

        try:
            cuisine_name = self.scraper.cuisine()
        except Exception:
            cuisine_name = None

        if cuisine_name:
            from apps.recipes.models import Cuisine

            cuisine, _ = Cuisine.objects.get_or_create(name=cuisine_name)
            recipe.cuisine = cuisine
            recipe.save(update_fields=["cuisine"])

        recipe.save()
        update_recipe_nutrition(recipe)
        return recipe

    def to_json(self, **kwargs):
        return self.scraper.to_json(**kwargs)
