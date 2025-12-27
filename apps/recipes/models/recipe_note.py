from django.db import models

class RecipeNote(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
    )

    content = models.TextField(blank=True, null=True)

    ordering = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordering", "id"]
        indexes = [
            models.Index(fields=["recipe"]),
        ]

    def __str__(self):
        return f"Note for {self.recipe}"
