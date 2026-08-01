from django.db import models
from django.utils.translation import gettext_lazy as _

class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE, verbose_name=_("Ingredient"))
    quantity = models.FloatField(verbose_name=_("Quantity"))
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT, verbose_name=_("Unit"))

    group = models.ForeignKey('RecipeIngredientGroup', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Group"))

    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        ordering = ['group__order', 'order']
        verbose_name = _("Recipe Ingredient")
        verbose_name_plural = _("Recipe Ingredients")

    def __str__(self):
        group_name = f" ({self.group.name})" if self.group else ""
        return f"{self.quantity} {self.unit} {self.ingredient.name}{group_name}"
