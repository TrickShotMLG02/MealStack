from apps.recipes.models import Recipe, RecipeIngredient, RecipeNutrition

def update_recipe_nutrition(recipe: Recipe) -> RecipeNutrition:
    """
    Calculate total and per-serving nutrition for a recipe.
    Assumes each ingredient has kcal, protein, fat, saturates, carbs, sugar, salt per 100g
    and units have grams_per_unit or density for volume conversions.
    Supports multiple IngredientGroups per recipe.
    """
    total_kcal = total_protein = total_fat = total_saturates = total_carbs = total_sugar = total_salt = 0

    # Get all RecipeIngredient objects via groups
    ingredients = RecipeIngredient.objects.filter(
        group__recipe=recipe
    ).select_related('ingredient', 'unit', 'group')

    for ri in ingredients:
        ingredient = ri.ingredient
        unit = ri.unit
        quantity = ri.quantity

        # Convert quantity to grams
        if unit.type == 'weight' and unit.grams_per_unit:
            grams = quantity * unit.grams_per_unit
        elif unit.type == 'volume' and unit.ml_per_unit and ingredient.density:
            grams = quantity * unit.ml_per_unit * ingredient.density
        elif unit.type == 'count':
            # If unit counts, assume grams_per_unit or fallback
            grams = quantity * (unit.grams_per_unit or 0)
        else:
            grams = 0  # unknown conversion

        factor = grams / 100  # nutrition per 100g
        total_kcal += ingredient.kcal * factor
        total_protein += ingredient.protein * factor
        total_fat += ingredient.fat * factor
        total_saturates += ingredient.saturates * factor
        total_carbs += ingredient.carbs * factor
        total_sugar += ingredient.sugar * factor
        total_salt += ingredient.salt * factor

    # Get or create RecipeNutrition
    nutrition, _ = RecipeNutrition.objects.get_or_create(recipe=recipe)

    nutrition.total_kcal = total_kcal
    nutrition.total_protein = total_protein
    nutrition.total_fat = total_fat
    nutrition.total_saturates = total_saturates
    nutrition.total_carbs = total_carbs
    nutrition.total_sugar = total_sugar
    nutrition.total_salt = total_salt

    if recipe.servings > 0:
        nutrition.per_serving_kcal = total_kcal / recipe.servings
        nutrition.per_serving_protein = total_protein / recipe.servings
        nutrition.per_serving_fat = total_fat / recipe.servings
        nutrition.per_serving_saturates = total_saturates / recipe.servings
        nutrition.per_serving_carbs = total_carbs / recipe.servings
        nutrition.per_serving_sugar = total_sugar / recipe.servings
        nutrition.per_serving_salt = total_salt / recipe.servings
    else:
        nutrition.per_serving_kcal = 0
        nutrition.per_serving_protein = 0
        nutrition.per_serving_fat = 0
        nutrition.per_serving_saturates = 0
        nutrition.per_serving_carbs = 0
        nutrition.per_serving_sugar = 0
        nutrition.per_serving_salt = 0

    nutrition.save()
    return nutrition