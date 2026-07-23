from django.http import JsonResponse
from django.db.models import Prefetch
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext as _
from urllib.parse import urlencode

from apps.recipes.models import Recipe, RecipeImage
from apps.recipes.selectors import search_recipes, search_suggestions

def recipe_list(request):
    search_query = (request.GET.get("q") or "").strip()
    search_kind = (request.GET.get("kind") or "").strip().lower() or None
    prefetches = [
        Prefetch(
            'recipeimage_set',
            queryset=RecipeImage.objects.all().order_by('-is_primary', 'ordering'),
            to_attr='images',
        ),
    ]

    if search_query:
        prefetches.extend(
            [
                'tags',
                'recipeingredientgroup_set__recipeingredient_set__ingredient',
                'recipestepgroup_set__recipestep_set',
                'recipenote_set',
            ]
        )

    recipes = (
        Recipe.objects.filter(status='published')
        .select_related("cuisine")
        .prefetch_related(*prefetches)
        .order_by('-created_at')
    )

    recipes = search_recipes(recipes, search_query, kind=search_kind)

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

    return render(request, 'recipes/recipe_list.html', {
        'recipes': recipes,
        'search_query': search_query,
    })


def recipe_search_suggestions(request):
    query = (request.GET.get("q") or "").strip()
    suggestions = []

    for suggestion in search_suggestions(query):
        if suggestion.kind == "recipe" and suggestion.recipe_slug:
            href = reverse("recipes:recipe_detail", args=[suggestion.recipe_slug])
        else:
            query_params = {"q": suggestion.value}
            if suggestion.kind in {"ingredient", "tag", "cuisine"}:
                query_params["kind"] = suggestion.kind

            href = f"{reverse('recipes:recipe_list')}?{urlencode(query_params)}"

        suggestions.append(
            {
                "kind": suggestion.kind,
                "kind_label": {
                    "recipe": _("Recipe"),
                    "tag": _("Tag"),
                    "cuisine": _("Cuisine"),
                    "ingredient": _("Ingredient"),
                }.get(suggestion.kind, suggestion.kind.title()),
                "label": suggestion.label,
                "href": href,
            }
        )

    return JsonResponse({"suggestions": suggestions})
