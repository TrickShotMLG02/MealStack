from django.db import models

class RecipeStep(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveIntegerField(default=0)
    description = models.TextField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Step {self.order} - {self.recipe.title}"
