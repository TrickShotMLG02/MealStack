from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch

from apps.recipes.models import (
    Recipe,
    RecipeComponent,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeStep,
    RecipeStepGroup,
)


MAX_COMPOSITION_DEPTH = 10


class CompositionError(ValueError):
    """Raised when a recipe tree cannot be rendered safely."""


@dataclass(frozen=True)
class ComposedIngredient:
    ingredient: object
    unit: object
    quantity: float


@dataclass(frozen=True)
class ComposedIngredientGroup:
    name: str | None
    ingredients: tuple[ComposedIngredient, ...]


@dataclass(frozen=True)
class ComposedStepGroup:
    name: str | None
    steps: tuple[object, ...]


@dataclass(frozen=True)
class RecipeSection:
    title: str
    recipe: Recipe
    ingredient_groups: tuple[ComposedIngredientGroup, ...]
    step_groups: tuple[ComposedStepGroup, ...]
    is_component: bool = False


@dataclass
class NutritionSummary:
    total_kcal: float = 0
    total_protein: float = 0
    total_fat: float = 0
    total_saturates: float = 0
    total_carbs: float = 0
    total_sugar: float = 0
    total_salt: float = 0
    per_serving_kcal: float = 0
    per_serving_protein: float = 0
    per_serving_fat: float = 0
    per_serving_saturates: float = 0
    per_serving_carbs: float = 0
    per_serving_sugar: float = 0
    per_serving_salt: float = 0

    def finalize(self, servings: float) -> "NutritionSummary":
        divisor = servings if servings > 0 else 1
        self.per_serving_kcal = self.total_kcal / divisor
        self.per_serving_protein = self.total_protein / divisor
        self.per_serving_fat = self.total_fat / divisor
        self.per_serving_saturates = self.total_saturates / divisor
        self.per_serving_carbs = self.total_carbs / divisor
        self.per_serving_sugar = self.total_sugar / divisor
        self.per_serving_salt = self.total_salt / divisor
        return self


@dataclass(frozen=True)
class RecipeComposition:
    recipe: Recipe
    sections: tuple[RecipeSection, ...]
    nutrition: NutritionSummary | None
    preparation_time: timedelta
    cooking_time: timedelta
    resting_time: timedelta
    total_time: timedelta

    @property
    def has_ingredients(self) -> bool:
        return any(
            group.ingredients
            for section in self.sections
            for group in section.ingredient_groups
        )

    @property
    def has_steps(self) -> bool:
        return any(
            group.steps
            for section in self.sections
            for group in section.step_groups
        )


_NUTRITION_FIELDS = (
    "kcal",
    "protein",
    "fat",
    "saturates",
    "carbs",
    "sugar",
    "salt",
)


def _recipe_content_queryset():
    return Recipe.objects.select_related("recipe_nutrition", "cuisine").prefetch_related(
        Prefetch(
            "recipeingredientgroup_set",
            queryset=RecipeIngredientGroup.objects.prefetch_related(
                Prefetch(
                    "recipeingredient_set",
                    queryset=RecipeIngredient.objects.select_related("ingredient", "unit").order_by("order"),
                )
            ).order_by("order"),
            to_attr="prefetched_ingredient_groups",
        ),
        Prefetch(
            "recipestepgroup_set",
            queryset=RecipeStepGroup.objects.prefetch_related(
                Prefetch("recipestep_set", queryset=RecipeStep.objects.order_by("order"))
            ).order_by("order"),
            to_attr="prefetched_step_groups",
        ),
        Prefetch(
            "components",
            queryset=RecipeComponent.objects.select_related("child_recipe").order_by("order", "id"),
            to_attr="prefetched_components",
        ),
    )


def _load_recipe(recipe_id: int) -> Recipe:
    return _recipe_content_queryset().get(pk=recipe_id)


def _ingredient_groups(recipe: Recipe):
    return getattr(recipe, "prefetched_ingredient_groups", None) or recipe.recipeingredientgroup_set.all()


def _step_groups(recipe: Recipe):
    return getattr(recipe, "prefetched_step_groups", None) or recipe.recipestepgroup_set.all()


def _components(recipe: Recipe):
    return getattr(recipe, "prefetched_components", None) or recipe.components.select_related("child_recipe").order_by("order", "id")


def _nutrition(recipe: Recipe):
    try:
        return recipe.recipe_nutrition
    except ObjectDoesNotExist:
        return None


def _add_nutrition(summary: NutritionSummary, nutrition, scale: float) -> bool:
    if nutrition is None:
        return False

    for field in _NUTRITION_FIELDS:
        setattr(
            summary,
            f"total_{field}",
            getattr(summary, f"total_{field}") + getattr(nutrition, f"total_{field}") * scale,
        )
    return True


def compose_recipe(
    recipe: Recipe,
    *,
    require_published: bool = False,
    max_depth: int = MAX_COMPOSITION_DEPTH,
) -> RecipeComposition:
    """Return a fully expanded, serving-normalized recipe composition.

    Quantities and nutrition are normalized to the root recipe's native
    servings. The public serving control and PDF exporter can then scale every
    line consistently using ``target / root.servings``.

    Preparation, cooking, and resting time are calculated as parallel tracks:
    the slowest track among the parent and all components determines each
    category, then the categories are added for the displayed total.
    """
    sections: list[RecipeSection] = []
    summary = NutritionSummary()
    nutrition_available = False
    preparation_times: list[timedelta] = []
    cooking_times: list[timedelta] = []
    resting_times: list[timedelta] = []
    visiting: set[int] = set()

    def visit(current: Recipe, scale_to_root: float, depth: int, title: str, is_component: bool):
        nonlocal nutrition_available

        if depth > max_depth:
            raise CompositionError(f"Recipe composition exceeds the maximum depth of {max_depth}.")
        if current.pk in visiting:
            raise CompositionError("Recipe composition contains a circular reference.")
        if require_published and current.status != "published":
            raise CompositionError("A published recipe contains an unpublished linked recipe.")

        visiting.add(current.pk)
        ingredient_groups = []
        for group in _ingredient_groups(current):
            ingredients = tuple(
                ComposedIngredient(
                    ingredient=recipe_ingredient.ingredient,
                    unit=recipe_ingredient.unit,
                    quantity=recipe_ingredient.quantity * scale_to_root,
                )
                for recipe_ingredient in group.recipeingredient_set.all()
            )
            if ingredients:
                ingredient_groups.append(
                    ComposedIngredientGroup(name=group.name, ingredients=ingredients)
                )
        step_groups = []
        for group in _step_groups(current):
            steps = tuple(group.recipestep_set.all())
            if steps:
                step_groups.append(ComposedStepGroup(name=group.name, steps=steps))
        sections.append(
            RecipeSection(
                title=title,
                recipe=current,
                ingredient_groups=tuple(ingredient_groups),
                step_groups=tuple(step_groups),
                is_component=is_component,
            )
        )

        preparation_times.append(current.preparation_time or timedelta())
        cooking_times.append(current.cooking_time or timedelta())
        resting_times.append(current.resting_time or timedelta())

        nutrition_available = _add_nutrition(summary, _nutrition(current), scale_to_root) or nutrition_available

        for component in _components(current):
            child = component.child_recipe
            # The related object from the component queryset does not carry
            # the recursive content prefetches, so reload it once per node.
            child = _load_recipe(child.pk)
            child_servings = child.servings if child.servings > 0 else 1
            used_servings = component.servings * scale_to_root
            child_scale_to_root = used_servings / child_servings
            child_title = component.title_override.strip() or child.title
            visit(child, child_scale_to_root, depth + 1, child_title, True)

        visiting.remove(current.pk)

    visit(recipe, 1.0, 0, recipe.title, False)

    nutrition = summary.finalize(recipe.servings) if nutrition_available else None
    preparation_time = max(preparation_times, default=timedelta())
    cooking_time = max(cooking_times, default=timedelta())
    resting_time = max(resting_times, default=timedelta())

    return RecipeComposition(
        recipe=recipe,
        sections=tuple(sections),
        nutrition=nutrition,
        preparation_time=preparation_time,
        cooking_time=cooking_time,
        resting_time=resting_time,
        total_time=preparation_time + cooking_time + resting_time,
    )
