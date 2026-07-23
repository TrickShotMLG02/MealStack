from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from apps.recipes.models import Recipe, RecipeImage, RecipeIngredient, RecipeIngredientGroup, RecipeNote, RecipeStep, RecipeStepGroup

def recipe_detail(request, slug):
    recipe = get_object_or_404(
        Recipe.objects.select_related("cuisine", "recipe_nutrition").prefetch_related(
            "tags",
            Prefetch(
                "recipeimage_set",
                queryset=RecipeImage.objects.all().order_by("-is_primary", "ordering"),
                to_attr="prefetched_images",
            ),
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
                    Prefetch(
                        "recipestep_set",
                        queryset=RecipeStep.objects.order_by("order"),
                    )
                ).order_by("order"),
                to_attr="prefetched_step_groups",
            ),
            Prefetch(
                "recipenote_set",
                queryset=RecipeNote.objects.order_by("ordering", "id"),
                to_attr="prefetched_notes",
            ),
        ),
        slug=slug,
    )

    images = getattr(recipe, "prefetched_images", None) or recipe.images_or_placeholder
    ingredient_count = sum(
        len(group.recipeingredient_set.all())
        for group in getattr(recipe, "prefetched_ingredient_groups", [])
    )
    step_count = sum(
        len(group.recipestep_set.all())
        for group in getattr(recipe, "prefetched_step_groups", [])
    )

    return render(request, "recipes/recipe_detail.html", {
        "recipe": recipe,
        "images": images,
        "nutrition": getattr(recipe, "recipe_nutrition", None),
        "notes": getattr(recipe, "prefetched_notes", []),
        "ingredient_groups": getattr(recipe, "prefetched_ingredient_groups", []),
        "step_groups": getattr(recipe, "prefetched_step_groups", []),
        "ingredient_count": ingredient_count,
        "step_count": step_count,
    })
