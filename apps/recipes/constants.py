from enum import Enum

class UnitType(str, Enum):
    WEIGHT = "weight",
    VOLUME = "volume",
    COUNT = "count",


class MeasurementUnitType(str, Enum):
    # (unit name, type, factor to base unit)
    GRAM = ("gram", UnitType.WEIGHT, 1)
    KILOGRAM = ("kilogram", UnitType.WEIGHT, 1000)
    MILLILITER = ("ml", UnitType.VOLUME, 1)
    LITER = ("liter", UnitType.VOLUME, 1000)
    TEASPOON = ("tsp", UnitType.VOLUME, 5)         # 1 tsp = 5 ml
    TABLESPOON = ("tbsp", UnitType.VOLUME, 15)     # 1 tbsp = 15 ml
    CUP = ("cup", UnitType.VOLUME, 240)            # 1 cup = 240 ml TODO: Check this
    PIECE = ("pcs", UnitType.COUNT, 1)
    NOT_FOUND = ("not_found", UnitType.COUNT, 0)   # inform user to take manual action

    def __new__(cls, value, unit_type, factor):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.unit_type = unit_type  # weight / volume / count
        obj.factor = factor  # factor to base unit
        return obj
