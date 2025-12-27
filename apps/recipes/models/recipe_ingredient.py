from django.db import models

class RecipeIngredient(models.Model):
    #recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT)

    group = models.ForeignKey('IngredientGroup', on_delete=models.CASCADE, null=True, blank=True)

    order = models.PositiveIntegerField(default=0)  # optional for display ordering

    class Meta:
        #unique_together = ('ingredient', 'unit', 'group',) #'recipe')
        ordering = ['group__order', 'order'] # order by group first, then item

    def __str__(self):
        group_name = f" ({self.group.name})" if self.group else ""
        return f"{self.quantity} {self.unit} {self.ingredient.name}{group_name}"
