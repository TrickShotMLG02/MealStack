from types import SimpleNamespace


def coerce_servings(value, fallback: int) -> int:
    try:
        servings = int(value)
    except (TypeError, ValueError):
        return fallback

    return max(1, servings)


def scale_quantity(quantity: float, base_servings: int, target_servings: int) -> float:
    if base_servings <= 0:
        base_servings = 1

    return quantity * target_servings / base_servings


def scale_nutrition(nutrition, target_servings: int):
    if not nutrition:
        return SimpleNamespace(
            servings=target_servings,
            kcal=0,
            protein=0,
            fat=0,
            carbs=0,
            sugar=0,
            salt=0,
        )

    return SimpleNamespace(
        servings=target_servings,
        kcal=nutrition.per_serving_kcal * target_servings,
        protein=nutrition.per_serving_protein * target_servings,
        fat=nutrition.per_serving_fat * target_servings,
        carbs=nutrition.per_serving_carbs * target_servings,
        sugar=nutrition.per_serving_sugar * target_servings,
        salt=nutrition.per_serving_salt * target_servings,
    )
