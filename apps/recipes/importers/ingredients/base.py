from abc import ABC, abstractmethod

from apps.recipes.models import Ingredient


class BaseIngredientImporter(ABC):
    """
    Abstract base class for all ingredient importers
    """

    @abstractmethod
    def import_ingredient(self, ean: str = "") -> Ingredient:
        """
        Import an ingredient with nutrition values from the given EAN and return the Ingredient object
        """
        pass


class IngredientImporterError(Exception):
    """Base exception for importer errors."""
    default_message = "Ingredient Importer error occurred"

    def __init__(self, value=None, message=None):
        self.value = value
        self.message = message or self.default_message
        super().__init__(self.message)


class EANNotFound(IngredientImporterError):
    """Raised when a required field is missing."""
    default_message = "Product not found for EAN"

    def __init__(self, ean):
        super().__init__(
            message=f"{self.default_message}: {ean}",
            value=ean,
        )