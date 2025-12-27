import json
import re

from recipe_scrapers import scrape_me
from .base import BaseRecipeImporter
from apps.recipes.models import (
    Recipe, RecipeIngredient, RecipeStep,
    Ingredient, Unit, Tag
)
from apps.recipes.services.nutrition import update_recipe_nutrition
from ..constants import MeasurementUnitType
from ..models import IngredientGroup


class ChefkochImporter(BaseRecipeImporter):
    """
    Import recipes from chefkoch.de using recipe-scrapers.
    """

    def __init__(self, url: str):
        self.url = url
        self.scraper = scrape_me(url)

    # Map common units from scraped text to your Unit names
    UNIT_MAP = {
        "g": "gram",
        "kg": "gram",
        "ml": "ml",
        "l": "ml",
        "tl": "ml",   # teaspoon
        "el": "ml",   # tablespoon
        "cup": "ml",
        "stück": "pcs",
        "": "pcs",
    }

    UNIT_MAP = {
        "g": MeasurementUnitType.GRAM,
        "kg": MeasurementUnitType.KILOGRAM,
        "ml": MeasurementUnitType.MILLILITER,
        "l": MeasurementUnitType.LITER,
        "tl": MeasurementUnitType.TEASPOON,
        "el": MeasurementUnitType.TABLESPOON,
        "cup": MeasurementUnitType.CUP,
        "stück": MeasurementUnitType.PIECE,
        "": MeasurementUnitType.NOT_FOUND,
    }

    def import_recipe(self) -> Recipe:
        # TODO: handle existing ingredients, recipes ect

        # Create Recipe
        raw_yields = self.scraper.yields()
        servings = 1  # default
        if raw_yields:
            # extract the first number (integer) from the string
            match = re.search(r"\d+", raw_yields)
            if match:
                servings = int(match.group())

        # normalize title by removing "von <author>" from recipe title
        title = str(self.scraper.title())
        title = title.replace(f"von {self.scraper.author()}", "").strip()

        recipe = Recipe.objects.create(
            title=title,
            servings=servings,
            status="draft",
            source=self.url,
            author=self.scraper.author(),
        )

        # Add Steps
        for i, step_text in enumerate(self.scraper.instructions_list(), start=1):
            step_text = step_text.strip()
            if step_text:
                RecipeStep.objects.create(
                    recipe=recipe,
                    order=i,
                    description=step_text
                )

        # Add Ingredients
        ingredient_groups = self.scraper.ingredient_groups()

        for i, group in enumerate(ingredient_groups):
            group_name = group.purpose
            group_ingredients = group.ingredients
            ingredient_group = IngredientGroup.objects.create(
                recipe=recipe,
                name=group_name,
                order=i,
            )

            for raw in group_ingredients:
                quantity, unit_raw, name = self.normalize_ingredient(raw)
                unit_name = self.UNIT_MAP.get(unit_raw.lower(), "count")
                unit, _ = Unit.objects.get_or_create(name=unit_name)
                ingredient, _ = Ingredient.objects.get_or_create(name=name)
                RecipeIngredient.objects.create(
                    #recipe=recipe,
                    ingredient=ingredient,
                    quantity=quantity,
                    unit=unit,
                    group=ingredient_group,
                )

        # Add Tags (optional)
        for tag_name in self.scraper.keywords():
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            recipe.tags.add(tag)

        # Optional: store image URL in a field if you have one
        # recipe.image_url = scraper.image()
        # recipe.save()

        # Recalculate nutrition using your service
        update_recipe_nutrition(recipe)

        return recipe

    def normalize_ingredient(self, text: str):
        """
        Simple heuristic to extract quantity, unit, and ingredient name.
        Example formats:
            "100 g Zucker" -> 100, g, Zucker
            "1 EL Öl" -> 1, EL, Öl
            "2 Stück Eier" -> 2, Stück, Eier
            "Salz" -> 1, count, Salz
        """
        parts = text.split()
        try:
            quantity = float(parts[0].replace(",", "."))
            unit = parts[1] if len(parts) > 2 else ""
            name = " ".join(parts[2:]) if len(parts) > 2 else parts[1]
        except (ValueError, IndexError):
            quantity = 1
            unit = ""
            name = text

        name = self.normalize_ingredient_name(name)
        unit = unit.rstrip(",.;:!? ")

        # TODO: Convert EL to ml ect
        return quantity, unit, name

    def to_json(self, **kwargs):
        """
        Return the JSON string produced by recipe-scrapers.
        Accepts kwargs for json.dumps (like indent, ensure_ascii, etc.).
        """
        # .to_json() returns a JSON string
        raw_json = self.scraper.to_json()

        # Optionally pretty-print / pass kwargs
        return json.dumps(raw_json, **kwargs)
