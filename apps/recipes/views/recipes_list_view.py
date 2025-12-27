from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from apps.recipes.models import Recipe, RecipeImage

def recipe_list(request):
    # Only show published recipes
    # TODO: Filter by status='published'
    recipes = Recipe.objects.filter(status='draft').order_by('-created_at')

    # Prefetch images ordered by primary first
    images_prefetch = Prefetch(
        'recipeimage_set',
        queryset=RecipeImage.objects.all().order_by('-is_primary', 'ordering'),
        to_attr='images'  # will be available as `recipe.images` instead of `recipe.recipeimage_set.all()`
    )
    recipes = recipes.prefetch_related(images_prefetch)

    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})
