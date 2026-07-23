import re
from fractions import Fraction

from apps.recipes.constants import UnitType


UNIT_CATALOG = [
    {"name": "gram", "type": UnitType.WEIGHT.value, "grams_per_unit": 1},
    {"name": "kilogram", "type": UnitType.WEIGHT.value, "grams_per_unit": 1000},
    {"name": "ml", "type": UnitType.VOLUME.value, "ml_per_unit": 1},
    {"name": "liter", "type": UnitType.VOLUME.value, "ml_per_unit": 1000},
    {"name": "tsp", "type": UnitType.VOLUME.value, "ml_per_unit": 5},
    {"name": "tbsp", "type": UnitType.VOLUME.value, "ml_per_unit": 15},
    {"name": "cup", "type": UnitType.VOLUME.value, "ml_per_unit": 240},
    {"name": "oz", "type": UnitType.WEIGHT.value, "grams_per_unit": 28.3495},
    {"name": "lb", "type": UnitType.WEIGHT.value, "grams_per_unit": 453.592},
    {"name": "pcs", "type": UnitType.COUNT.value, "grams_per_unit": 30},
]

TAG_CATALOG = [
    "Breakfast",
    "Brunch",
    "Dessert",
    "Dinner",
    "Italian",
    "Pasta",
    "Pancakes",
    "Vegetarian",
    "Vegan",
    "Gluten Free",
    "Dairy Free",
    "Chicken",
    "Comfort Food",
    "Sweet",
]

INGREDIENT_CATALOG = {
    "flour": {"kcal": 364, "carbs": 76, "protein": 10, "fat": 1, "salt": 0.01},
    "milk": {"kcal": 60, "carbs": 5, "protein": 3.2, "fat": 3.3, "salt": 0.1, "density": 1.03},
    "egg": {"kcal": 155, "carbs": 1.1, "protein": 13, "fat": 11, "salt": 0.37},
    "butter": {"kcal": 717, "carbs": 0.1, "protein": 0.9, "fat": 81, "salt": 1.5},
    "oil": {"kcal": 884, "carbs": 0, "protein": 0, "fat": 100, "salt": 0, "density": 0.92},
    "olive oil": {"kcal": 884, "carbs": 0, "protein": 0, "fat": 100, "salt": 0, "density": 0.91},
    "sunflower oil": {"kcal": 884, "carbs": 0, "protein": 0, "fat": 100, "salt": 0, "density": 0.92},
    "vegetable oil": {"kcal": 884, "carbs": 0, "protein": 0, "fat": 100, "salt": 0, "density": 0.92},
    "sugar": {"kcal": 387, "carbs": 100, "protein": 0, "fat": 0, "salt": 0},
    "brown sugar": {"kcal": 380, "carbs": 98, "protein": 0, "fat": 0, "salt": 0},
    "blueberries": {"kcal": 57, "carbs": 14, "protein": 0.7, "fat": 0.3, "sugar": 10},
    "banana": {"kcal": 89, "carbs": 23, "protein": 1.1, "fat": 0.3, "sugar": 12},
    "lemon": {"kcal": 29, "carbs": 9, "protein": 1.1, "fat": 0.3, "sugar": 2.5},
    "baking powder": {"kcal": 53, "carbs": 28, "protein": 0, "fat": 0, "salt": 11},
    "baking soda": {"kcal": 0, "carbs": 0, "protein": 0, "fat": 0, "salt": 27},
    "salt": {"kcal": 0, "carbs": 0, "protein": 0, "fat": 0, "salt": 100},
    "pepper": {"kcal": 251, "carbs": 64, "protein": 10, "fat": 3.3, "salt": 0.01},
    "tomatoes": {"kcal": 18, "carbs": 3.9, "protein": 0.9, "fat": 0.2, "sugar": 2.6, "salt": 0.01},
    "onion": {"kcal": 40, "carbs": 9.3, "protein": 1.1, "fat": 0.1, "sugar": 4.2, "salt": 0.01},
    "garlic": {"kcal": 149, "carbs": 33, "protein": 6.4, "fat": 0.5, "sugar": 1, "salt": 0.02},
    "oregano": {"kcal": 265, "carbs": 69, "protein": 9, "fat": 4.3, "salt": 0.02},
    "basil": {"kcal": 23, "carbs": 2.7, "protein": 3.2, "fat": 0.6, "salt": 0.02},
    "ricotta cheese": {"kcal": 174, "carbs": 3, "protein": 11, "fat": 13, "salt": 0.3},
    "mozzarella cheese": {"kcal": 280, "carbs": 2.2, "protein": 28, "fat": 17, "salt": 0.6},
    "parmesan": {"kcal": 431, "carbs": 4.1, "protein": 38, "fat": 29, "salt": 1.5},
    "breadcrumbs": {"kcal": 395, "carbs": 72, "protein": 13, "fat": 5, "salt": 1.2},
    "chicken": {"kcal": 165, "carbs": 0, "protein": 31, "fat": 3.6, "salt": 0.2},
    "italian sausage": {"kcal": 301, "carbs": 2, "protein": 14, "fat": 26, "salt": 1.5},
    "pesto": {"kcal": 440, "carbs": 5, "protein": 5, "fat": 45, "salt": 2.2},
    "marinara sauce": {"kcal": 60, "carbs": 10, "protein": 2, "fat": 2, "salt": 0.8},
    "red pepper flakes": {"kcal": 318, "carbs": 56, "protein": 12, "fat": 17, "salt": 0.02},
}

INGREDIENT_ALIASES = [
    ("self raising flour", "flour"),
    ("self-raising flour", "flour"),
    ("all purpose flour", "flour"),
    ("all-purpose flour", "flour"),
    ("plain flour", "flour"),
    ("whole milk", "milk"),
    ("large egg", "egg"),
    ("large eggs", "egg"),
    ("egg", "egg"),
    ("eggs", "egg"),
    ("sunflower or vegetable oil", "vegetable oil"),
    ("vegetable oil", "vegetable oil"),
    ("sunflower oil", "sunflower oil"),
    ("olive oil", "olive oil"),
    ("caster sugar", "sugar"),
    ("granulated sugar", "sugar"),
    ("brown sugar", "brown sugar"),
    ("blueberry", "blueberries"),
    ("blueberries", "blueberries"),
    ("banana", "banana"),
    ("bananas", "banana"),
    ("lemon wedges", "lemon"),
    ("lemon", "lemon"),
    ("bicarbonate of soda", "baking soda"),
    ("baking soda", "baking soda"),
    ("baking powder", "baking powder"),
    ("kosher salt", "salt"),
    ("sea salt", "salt"),
    ("salt", "salt"),
    ("freshly ground black pepper", "pepper"),
    ("freshly ground pepper", "pepper"),
    ("black pepper", "pepper"),
    ("pepper", "pepper"),
    ("crushed tomatoes", "tomatoes"),
    ("diced tomatoes", "tomatoes"),
    ("tomatoes", "tomatoes"),
    ("fresh basil leaves", "basil"),
    ("basil leaves", "basil"),
    ("basil", "basil"),
    ("ricotta cheese", "ricotta cheese"),
    ("mozzarella cheese", "mozzarella cheese"),
    ("parmesan cheese", "parmesan"),
    ("parmesan", "parmesan"),
    ("breadcrumbs", "breadcrumbs"),
    ("bread crumbs", "breadcrumbs"),
    ("chicken thighs", "chicken"),
    ("chicken breast", "chicken"),
    ("chicken breasts", "chicken"),
    ("spicy italian sausage", "italian sausage"),
    ("italian sausage", "italian sausage"),
    ("sun-dried tomato pesto", "pesto"),
    ("tomato pesto", "pesto"),
    ("marinara sauce", "marinara sauce"),
    ("red pepper flakes", "red pepper flakes"),
    ("garlic cloves", "garlic"),
    ("garlic", "garlic"),
    ("onion", "onion"),
    ("onions", "onion"),
]

RECIPE_FIXTURES = [
    {
        "url": "https://www.bbcgoodfood.com/recipes/easy-pancakes",
        "tags": ["Breakfast", "Pancakes", "Vegetarian", "Sweet"],
    },
    {
        "url": "https://www.bbcgoodfood.com/recipes/american-pancakes",
        "tags": ["Breakfast", "Brunch", "Pancakes", "Vegetarian"],
    },
    {
        "url": "https://www.bbcgoodfood.com/recipes/banana-pancakes",
        "tags": ["Breakfast", "Gluten Free", "Pancakes", "Vegetarian"],
    },
    {
        "url": "https://www.bbcgoodfood.com/recipes/easy-vegan-pancakes",
        "tags": ["Breakfast", "Vegan", "Pancakes", "Dairy Free"],
    },
    {
        "url": "https://www.bbcgoodfood.com/recipes/perfect-pancakes-recipe",
        "tags": ["Breakfast", "Brunch", "Pancakes", "Vegetarian"],
    },
    {
        "url": "https://www.epicurious.com/recipes/food/views/lasagne-bolognese-51193620",
        "tags": ["Dinner", "Italian", "Pasta", "Comfort Food"],
    },
    {
        "url": "https://www.epicurious.com/recipes/food/views/lasagna-recipe",
        "tags": ["Dinner", "Italian", "Pasta", "Comfort Food"],
    },
    {
        "url": "https://www.epicurious.com/recipes/food/views/chicken-parmesan-51155020",
        "tags": ["Dinner", "Chicken", "Italian", "Comfort Food"],
    },
]

FRACTION_MAP = {
    "\u00bd": " 1/2",
    "\u00bc": " 1/4",
    "\u00be": " 3/4",
    "\u2153": " 1/3",
    "\u2154": " 2/3",
    "\u215b": " 1/8",
    "\u215c": " 3/8",
    "\u215d": " 5/8",
    "\u215e": " 7/8",
}

UNIT_ALIASES = {
    "g": "gram",
    "gram": "gram",
    "grams": "gram",
    "kg": "kilogram",
    "kilogram": "kilogram",
    "kilograms": "kilogram",
    "ml": "ml",
    "l": "liter",
    "liter": "liter",
    "liters": "liter",
    "litre": "liter",
    "litres": "liter",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "cup": "cup",
    "cups": "cup",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
}

COUNT_WORDS = {
    "large",
    "medium",
    "small",
    "big",
    "extra-large",
    "extra",
    "whole",
    "fresh",
    "freshly",
    "room-temperature",
    "room",
    "skinless",
    "boneless",
    "packed",
    "chopped",
    "coarsely",
    "finely",
    "prepared",
}


def normalize_text(value: str) -> str:
    value = value.strip()
    for source, replacement in FRACTION_MAP.items():
        value = value.replace(source, replacement)
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def parse_quantity(text: str) -> float:
    text = normalize_text(text).strip()
    parts = text.split()
    if len(parts) == 2 and "/" in parts[1]:
        return float(Fraction(parts[0]) + Fraction(parts[1]))
    if len(parts) == 1 and "/" in parts[0]:
        return float(Fraction(parts[0]))
    if len(parts) == 2:
        try:
            return float(parts[0]) + float(Fraction(parts[1]))
        except (ValueError, ZeroDivisionError):
            pass
    return float(text)


def canonicalize_ingredient_name(name: str) -> str:
    cleaned = normalize_text(name).lower()
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = cleaned.replace(".", "")
    cleaned = cleaned.replace("/", " ")
    cleaned = re.sub(r"\b(?:and|or)\b", " ", cleaned)
    cleaned = re.sub(
        r"\b(?:to serve|for serving|for frying|plus a little extra for frying|optional|as needed|warmed)\b.*$",
        "",
        cleaned,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:-")

    for alias, canonical in sorted(INGREDIENT_ALIASES, key=lambda item: len(item[0]), reverse=True):
        if alias in cleaned:
            return canonical

    if cleaned.endswith("s") and cleaned[:-1] in INGREDIENT_CATALOG:
        return cleaned[:-1]

    return cleaned


def parse_ingredient_line(raw_line: str) -> tuple[float, str, str]:
    line = normalize_text(raw_line)
    line = re.sub(r"^[Nn]/[Aa]\s+", "", line)
    line = re.sub(r"\s+", " ", line).strip(" ,;:.")

    count_prefix_match = re.match(
        r"^(?P<count>\d+(?:\.\d+)?)\s*(?:pcs?|pieces?|piece)\s+(?P<quantity>\d+(?:\.\d+)?)\s*(?P<unit>oz|lb|g|kg|ml|l|tsp|tbsp|cup|cups)\b\.?\s*(?P<rest>.+)$",
        line,
        flags=re.IGNORECASE,
    )
    if count_prefix_match:
        quantity = float(count_prefix_match.group("quantity"))
        unit = UNIT_ALIASES[count_prefix_match.group("unit").lower()]
        name = count_prefix_match.group("rest")
    else:
        compact_match = re.match(
            r"^(?P<quantity>\d+(?:\.\d+)?)(?P<unit>oz|lb|g|kg|ml|l|tsp|tbsp|cup|cups)\b\.?\s*(?P<rest>.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if compact_match:
            quantity = float(compact_match.group("quantity"))
            unit = UNIT_ALIASES[compact_match.group("unit").lower()]
            name = compact_match.group("rest")
        else:
            special_match = re.match(
                r"^(?P<quantity>\d+(?:\.\d+)?)\s*-\s*(?P<unit>oz|lb|g|kg|ml|l)\.?\s*(?P<rest>.+)$",
                line,
                flags=re.IGNORECASE,
            )
            if special_match:
                quantity = float(special_match.group("quantity"))
                unit = UNIT_ALIASES[special_match.group("unit").lower()]
                name = special_match.group("rest")
                if " plus " in name.lower():
                    name = re.split(r"\bplus\b", name, maxsplit=1, flags=re.IGNORECASE)[1]
                    name = re.sub(
                        r"^\d+(?:\.\d+)?\s*(?:cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|ml|l|g|kg|oz|lb)\s+",
                        "",
                        name,
                        flags=re.IGNORECASE,
                    )
                else:
                    name = re.sub(
                        r"^(?:can|container|containers|package|packages|pack|packs)\s+",
                        "",
                        name,
                        flags=re.IGNORECASE,
                    )
            else:
                quantity_match = re.match(
                    r"^(?P<quantity>\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+)\s+(?P<rest>.+)$",
                    line,
                )
                if quantity_match:
                    quantity = parse_quantity(quantity_match.group("quantity"))
                    rest = quantity_match.group("rest")
                else:
                    quantity = 1.0
                    rest = line

                rest_tokens = rest.split()
                unit = ""
                if rest_tokens:
                    first = rest_tokens[0].lower().strip(".,;:!?")
                    if first in UNIT_ALIASES:
                        unit = UNIT_ALIASES[first]
                        rest_tokens = rest_tokens[1:]
                    elif first in COUNT_WORDS:
                        unit = "pcs"
                        rest_tokens = rest_tokens[1:]

                name = " ".join(rest_tokens) if rest_tokens else rest

    name = re.split(
        r"\bplus\b|\bto serve\b|\bfor serving\b|\bfor frying\b",
        name,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    name = name.split(",")[0]
    name = normalize_text(name).strip(" ,;:.")
    name = canonicalize_ingredient_name(name)

    return quantity, unit or "pcs", name


def should_start_new_step_group(step_text: str) -> bool:
    cleaned = normalize_text(step_text).strip(" :.-")
    if not cleaned:
        return False
    if len(cleaned.split()) > 4:
        return False
    if any(ch in cleaned for ch in ".!?"):
        return False
    return cleaned[0].isupper()


def unit_defaults(name: str):
    for item in UNIT_CATALOG:
        if item["name"] == name:
            return {k: v for k, v in item.items() if k != "name"}
    return {}


def ingredient_defaults(name: str):
    return INGREDIENT_CATALOG.get(name, {})
