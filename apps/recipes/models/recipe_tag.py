from django.db import models

class RecipeTag(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('recipe', 'tag')

    def __str__(self):
        return f"{self.recipe} - {self.tag}"