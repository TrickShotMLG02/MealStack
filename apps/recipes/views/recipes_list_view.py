from django.http import JsonResponse
from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext as _
from urllib.parse import urlencode

from apps.recipes.models import Recipe, RecipeImage
from apps.users.models import RecipeBookmark
from apps.recipes.selectors import search_recipes, search_suggestions
from apps.common.rate_limiting import is_rate_limited

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

    recipe_list_items = list(recipes)
    bookmarked_ids = set()
    if request.user.is_authenticated:
        bookmarked_ids = set(RecipeBookmark.objects.filter(user=request.user, recipe_id__in=[recipe.pk for recipe in recipe_list_items]).values_list("recipe_id", flat=True))

    for recipe in recipe_list_items:
        primary_image = next(
            (
                image
                for image in getattr(recipe, "images", [])
                if image.is_primary and image.image
            ),
            None,
        )
        recipe.list_image_url = primary_image.image.url if primary_image else static("recipes/images/placeholder.jpg")
        recipe.is_bookmarked = recipe.pk in bookmarked_ids

    return render(request, 'recipes/recipe_list.html', {
        'recipes': recipe_list_items,
        'search_query': search_query,
    })


def recipe_search_suggestions(request):
    if is_rate_limited(
        request,
        key_prefix="recipe-search-suggestions",
        limit=settings.PUBLIC_SEARCH_RATE_LIMIT,
        window=settings.PUBLIC_RATE_LIMIT_WINDOW,
    ):
        return JsonResponse(
            {"error": "Too many search requests."},
            status=429,
            headers={"Retry-After": str(settings.PUBLIC_RATE_LIMIT_WINDOW)},
        )
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
