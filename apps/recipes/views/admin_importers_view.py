from django.shortcuts import render
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


IMPORTERS = [
    {
        "name": "Ingredient Importer",
        "url_path": "ingredient/",
        "view": ingredient_importer,
    },
]


def importers_home(request):
    """
    Landing page for all admin importers.
    """
    # Build context with links to all importers
    importers_list = [
        {
            "name": imp["name"],
            "url": f"/admin/importers/{imp['url_path']}"
        }
        for imp in IMPORTERS
    ]

    context = {
        "importers": importers_list,
    }

    return render(request, "admin/importers_home.html", context)