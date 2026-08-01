from apps.recipes.importers.recipes.base import BaseRecipeScraperImporter
from apps.recipes.importers.recipes.registry import register_recipe_importer


@register_recipe_importer(
    url_path="recipe/bbc-good-food/",
    base_domain="bbcgoodfood.com",
    url_patterns=(
        r"^https?://(?:www\.)?bbcgoodfood\.com/recipes/[^/?#]+/?(?:[?#].*)?$",
    ),
)
class BBCGoodFoodImporter(BaseRecipeScraperImporter):
    site_name = "BBC Good Food"
    url_placeholder = "https://www.bbcgoodfood.com/recipes/..."
