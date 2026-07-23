from apps.recipes.importers.ingredients.base import BaseIngredientImporter, EANNotFound
from apps.recipes.models import Ingredient
import openfoodfacts

class OpenFoodFactsImporter(BaseIngredientImporter):
    """
    Imports Ingredients from world.openfoodfacts.org
    """

    fields_to_fetch = [
        'code',
        'brands',
        'product_name',
        'product_name_de',
        'generic_name',
        'generic_name_de',
        'nutriments'
    ]

    def __init__(self, ean: str = ""):
        self.ean = ean
        self.api = openfoodfacts.API(user_agent="MealStack/1.0", country="de")

    def import_ingredient(self, ean: str = "") -> Ingredient:
        ean_code = ean if ean else self.ean
        res = self.api.product.get(ean_code, fields=self.fields_to_fetch)

        if not res:
            raise EANNotFound(ean_code)

        nutriments = res.get('nutriments')

        # extract values
        code = res.get('code')
        brands = res.get('brands').split(",")
        product_name = res.get('product_name_de') or res.get('product_name')
        generic_name = res.get('generic_name_de') or res.get('generic_name')

        kcal = nutriments.get('energy-kcal', 0)
        fat = nutriments.get('fat_100g', 0)
        saturated_fat = nutriments.get('saturated-fat_100g', 0)
        carbs = nutriments.get('carbohydrates_100g', 0)
        sugar = nutriments.get('sugar_100g', 0)
        proteins = nutriments.get('proteins_100g', 0)
        salt = nutriments.get('salt_100g', 0)

        ingredient, _ = Ingredient.objects.update_or_create(
            ean=code,
            defaults={
                "name": product_name,
                "generic_name": generic_name,
                "brand": brands[0],
                "kcal": kcal,
                "fat": fat,
                "saturates": saturated_fat,
                "carbs": carbs,
                "sugar": sugar,
                "protein": proteins,
                "salt": salt,
            },
        )
        return ingredient
