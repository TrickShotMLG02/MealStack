from django.db import models

from apps.recipes import UnitType


class Unit(models.Model):
    TYPE_CHOICES = [
        (UnitType.WEIGHT, 'Weight'),
        (UnitType.VOLUME, 'Volume'),
        (UnitType.COUNT, 'Count'),
    ]

    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    grams_per_unit = models.FloatField(null=True, blank=True)  # for weight/count
    ml_per_unit = models.FloatField(null=True, blank=True)  # for volume

    def to_grams(self, quantity: float, ingredient=None) -> float:
        """
        Convert a quantity of this unit to grams. Density required for volume conversions.
        """
        if self.type == 'weight':
            return quantity * (self.grams_per_unit or 1)
        elif self.type == 'volume':
            if ingredient and ingredient.density:
                return quantity * (self.ml_per_unit or 1) * ingredient.density
            raise ValueError(f"Cannot convert volume to weight without density for {ingredient}")
        elif self.type == 'count':
            return quantity * (self.grams_per_unit or 0)
        raise ValueError(f"Unknown unit type: {self.type}")

    def __str__(self):
        return self.name