from django.shortcuts import get_object_or_404, render
from apps.recipes.models import Recipe

def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug)
    images = recipe.recipeimage_set.all().order_by('-is_primary', 'ordering')

    return render(request, "recipes/recipe_detail.html", {
        "recipe": recipe,
        "images": images,
    })
