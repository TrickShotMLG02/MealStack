from apps.recipes.importers.recipes.base import BaseRecipeScraperImporter
from apps.recipes.importers.recipes.registry import register_recipe_importer


@register_recipe_importer(
    url_path="recipe/epicurious/",
    url_patterns=(
        r"^https?://(?:www\.)?epicurious\.com/recipes/food/views/[^/?#]+/?(?:[?#].*)?$",
    ),
)
class EpicuriousImporter(BaseRecipeScraperImporter):
    site_name = "Epicurious"
    url_placeholder = "https://www.epicurious.com/recipes/food/views/..."
