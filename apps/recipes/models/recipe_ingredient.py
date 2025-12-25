from django.db import models

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT)

    order = models.PositiveIntegerField(default=0)  # optional for display ordering

    class Meta:
        unique_together = ('recipe', 'ingredient', 'unit')
        ordering = ['order']

    def __str__(self):
        return f"{self.quantity} {self.unit} {self.ingredient.name}"
