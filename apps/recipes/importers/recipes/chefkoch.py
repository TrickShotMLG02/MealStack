from apps.recipes.importers.recipes.base import BaseRecipeScraperImporter


class ChefkochImporter(BaseRecipeScraperImporter):
    site_name = "Chefkoch"
    url_placeholder = "https://www.chefkoch.de/rezepte/..."

    def normalize_title(self, title: str) -> str:
        author = self._safe_text("author").strip()
        if author:
            title = title.replace(f"von {author}", "")
        return title.strip()
