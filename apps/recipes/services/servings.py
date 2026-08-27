from fractions import Fraction
import re
from types import SimpleNamespace


def coerce_servings(value, fallback: float) -> float:
    try:
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
            mixed_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s+(\d+)\/(\d+)", normalized)
            if mixed_match:
                whole, numerator, denominator = mixed_match.groups()
                servings = float(Fraction(whole) + Fraction(int(numerator), int(denominator)))
            else:
                servings = float(Fraction(normalized))
        else:
            servings = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return fallback

    return servings if servings > 0 else fallback


def scale_quantity(quantity: float, base_servings: float, target_servings: float) -> float:
    if base_servings <= 0:
        base_servings = 1

    return quantity * target_servings / base_servings


def scale_nutrition(nutrition, target_servings: float):
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
