from apps.recipes.importers.recipes.base import BaseRecipeScraperImporter


class EpicuriousImporter(BaseRecipeScraperImporter):
    site_name = "Epicurious"
    url_placeholder = "https://www.epicurious.com/recipes/food/views/..."
