from django.db import models

class RecipeStepGroup(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)  # e.g., "Salad", "Sauce"

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "Main"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name