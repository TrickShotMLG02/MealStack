from abc import ABC, abstractmethod
from apps.recipes.models import Recipe

class BaseRecipeImporter(ABC):
    """
    Abstract base class for all recipe importers.
    """

    @abstractmethod
    def import_recipe(self) -> Recipe:
        """
        Import a recipe from the given URL and return the Recipe object.
        """
        pass

    @staticmethod
    def normalize_ingredient(text: str):
        """
        Simple helper to parse quantity/unit/ingredient from raw text.
        Can be overridden or extended per website.
        """
        parts = text.split()
        try:
            quantity = float(parts[0])
            unit = parts[1] if len(parts) > 2 else ""
            name = " ".join(parts[2:]) if len(parts) > 2 else parts[1]
        except ValueError:
            quantity = 1
            unit = ""
            name = text
        return quantity, unit, name

    @abstractmethod
    def to_json(self) -> str:
        """
        Return the JSON string representation of the object.
        :return: JSON string
        """
        pass