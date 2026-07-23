from apps.recipes.importers.recipes.base import BaseRecipeScraperImporter


class BBCGoodFoodImporter(BaseRecipeScraperImporter):
    site_name = "BBC Good Food"
    url_placeholder = "https://www.bbcgoodfood.com/recipes/..."
