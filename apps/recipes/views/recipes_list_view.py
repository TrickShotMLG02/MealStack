from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
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

    for recipe in recipes:
        primary_image = next(
            (
                image
                for image in getattr(recipe, "images", [])
                if image.is_primary and image.image
            ),
            None,
        )
        recipe.list_image_url = primary_image.image.url if primary_image else static("recipes/images/placeholder.jpg")

    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})
