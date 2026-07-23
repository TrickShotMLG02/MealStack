from django.shortcuts import render

from apps.recipes.importers.recipes.chefkoch import ChefkochImporter
from apps.recipes.importers.ingredients.openfoodfacts import OpenFoodFactsImporter
from apps.recipes.importers.ingredients.base import EANNotFound


def ingredient_importer(request):
    message = None
    if request.method == "POST":
        ean = request.POST.get("ean")
        if ean:
            try:
                importer = OpenFoodFactsImporter(ean=ean)
                ingredient = importer.import_ingredient()
                message = f"Ingredient '{ingredient.name}' imported successfully!"
            except EANNotFound:
                message = f"EAN {ean} not found in OpenFoodFacts."
            except Exception as e:
                message = f"Error: {str(e)}"
        else:
            message = "Please provide a valid EAN."
    return render(request, "admin/ingredient_importer.html", {"message": message})


def recipe_importer(request):
    message = None
    if request.method == "POST":
        url = request.POST.get("url")
        if url:
            try:
                importer = ChefkochImporter(url=url)
                recipe = importer.import_recipe()
                message = f"Recipe '{recipe.title}' imported successfully!"
            except Exception as e:
                message = f"Error: {str(e)}"
        else:
            message = "Please provide a valid recipe URL."
    return render(request, "admin/recipe_importer.html", {"message": message})


INGREDIENT_IMPORTERS = [
    {
        "name": "OpenFoodFacts",
        "url_path": "ingredient/openfoodfacts/",
        "view": ingredient_importer,
    },
]

RECIPE_IMPORTERS = [
    {
        "name": "Chefkoch",
        "url_path": "recipe/chefkoch/",
        "view": recipe_importer,
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


def importers_home(request):
    return render(
        request,
        "admin/importers_home.html",
        {
            "section_title": "Importers",
            "importers": [
                {"name": "Ingredient Importers", "url": "/admin/importers/ingredient/"},
                {"name": "Recipe Importers", "url": "/admin/importers/recipe/"},
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
            "section_title": "Recipe Importers",
            "importers": _build_importers_list(RECIPE_IMPORTERS),
        },
    )
