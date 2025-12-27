from django.db import models

class RecipeStep(models.Model):
    #recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveIntegerField(default=0)
    description = models.TextField()

    group = models.ForeignKey('RecipeStepGroup', on_delete=models.CASCADE)

    class Meta:
        ordering = ['order']

    def __str__(self):
        group_name = f" ({self.group.name})" if self.group else ""
        return f"Step {self.order} {group_name}"
