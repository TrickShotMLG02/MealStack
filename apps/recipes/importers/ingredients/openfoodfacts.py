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
        'nutriments'
    ]

    def __init__(self, ean: str = ""):
        self.ean = ean
        self.api = openfoodfacts.API(user_agent="MealStack/1.0")

    def import_ingredient(self, ean: str = "") -> Ingredient:
        ean_code = ean if ean else self.ean
        res = self.api.product.get(ean_code, fields=self.fields_to_fetch)

        if not res:
            raise EANNotFound(ean_code)

        nutriments = res.get('nutriments')

        # extract values
        code = res.get('code')
        brands = res.get('brands').split(",")
        product_name = res.get('product_name')

        kcal = nutriments.get('energy-kcal', 0)
        proteins = nutriments.get('proteins_100g', 0)
        fat = nutriments.get('fat_100g', 0)
        saturated_fat = nutriments.get('saturated-fat_100g', 0)
        carbs = nutriments.get('carbohydrates_100g', 0)
        salt = nutriments.get('salt_100g', 0)
        sugar = nutriments.get('sugar_100g', 0)

        ingredient = Ingredient.objects.create(
            ean=code,
            name=product_name,
            brand=brands[0],

            kcal=kcal,
            protein=proteins,
            fat=fat,
            carbs=carbs,
            salt=salt,
        )

        ingredient.save()
        return ingredient