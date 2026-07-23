from django.utils.translation import gettext as _
from django.shortcuts import render

from apps.recipes.importers.ingredients.openfoodfacts import OpenFoodFactsImporter
from apps.recipes.importers.ingredients.base import EANNotFound
from apps.recipes.importers.recipes.registry import get_recipe_importers


def ingredient_importer(request):
    message = None
    if request.method == "POST":
        ean = request.POST.get("ean")
        if ean:
            try:
                importer = OpenFoodFactsImporter(ean=ean)
                ingredient = importer.import_ingredient()
                message = _("Ingredient '%(ingredient_name)s' imported successfully!") % {
                    "ingredient_name": ingredient.name,
                }
            except EANNotFound:
                message = _("EAN %(ean)s not found in OpenFoodFacts.") % {"ean": ean}
            except Exception as e:
                message = _("Error: %(error)s") % {"error": str(e)}
        else:
            message = _("Please provide a valid EAN.")
    return render(request, "admin/ingredient_importer.html", {"message": message})


def _recipe_importer_view(request, importer_spec):
    message = None
    if request.method == "POST":
        url = request.POST.get("url")
        if url:
            if not importer_spec.matches_url(url):
                message = _("Invalid URL for %(site_name)s. Please use a matching recipe URL.") % {
                    "site_name": importer_spec.name,
                }
            else:
                try:
                    importer = importer_spec.importer_cls(url=url)
                    recipe = importer.import_recipe()
                    message = _("Recipe '%(recipe_title)s' imported successfully!") % {
                        "recipe_title": recipe.title,
                    }
                except Exception as e:
                    message = _("Error importing recipe: %(error)s") % {"error": str(e)}
        else:
            message = _("Please provide a valid recipe URL.")
    return render(
        request,
        "admin/recipe_importer.html",
        {
            "message": message,
            "site_name": importer_spec.name,
            "url_placeholder": importer_spec.url_placeholder,
        },
    )


def make_recipe_importer_view(importer_spec):
    def view(request):
        return _recipe_importer_view(request, importer_spec)

    view.__name__ = importer_spec.name.lower().replace(" ", "_")
    return view


INGREDIENT_IMPORTERS = [
    {
        "name": "OpenFoodFacts",
        "url_path": "ingredient/openfoodfacts/",
        "view": ingredient_importer,
    },
]

def _build_importers_list(importers):
    return [
        {
            "name": imp["name"],
            "url": f"/admin/importers/{imp['url_path']}",
        }
        for imp in importers
    ]


def get_recipe_importer_entries():
    recipe_importers = get_recipe_importers()
    return [
        {
            "name": importer.name,
            "url_path": importer.url_path,
            "view": make_recipe_importer_view(importer),
        }
        for importer in recipe_importers
    ]


def importers_home(request):
    return render(
        request,
        "admin/importers_home.html",
        {
            "section_title": "Importers",
            "importers": [
                {"name": "Ingredient Importers", "url": "/admin/importers/ingredient/"},
                {"name": "Recipe Scrapers", "url": "/admin/importers/recipe/"},
            ],
        },
    )


def ingredient_importers_home(request):
    return render(
        request,
        "admin/importers_home.html",
        {
            "section_title": "Ingredient Importers",
            "importers": _build_importers_list(INGREDIENT_IMPORTERS),
        },
    )


def recipe_importers_home(request):
    return render(
        request,
        "admin/importers_home.html",
        {
            "section_title": "Recipe Scrapers",
            "importers": _build_importers_list(get_recipe_importer_entries()),
        },
    )
