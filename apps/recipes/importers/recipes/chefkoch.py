from typing import override

from apps.recipes.importers.recipes.base import BaseRecipeScraperImporter
from apps.recipes.importers.recipes.registry import register_recipe_importer


@register_recipe_importer(
    url_path="recipe/chefkoch/",
    url_patterns=(
        r"^https?://(?:www\.)?chefkoch\.de/rezepte/\d+/.+$",
    ),
)
class ChefkochImporter(BaseRecipeScraperImporter):
    site_name = "Chefkoch"
    url_placeholder = "https://www.chefkoch.de/rezepte/..."

    @override
    def normalize_title(self, title: str) -> str:
        author = self._safe_text("author").strip()
        if author:
            title = title.replace(f"von {author}", "")
        return title.strip()
