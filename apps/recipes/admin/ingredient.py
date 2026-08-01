from django.contrib import admin
from apps.recipes.models import Ingredient

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'kcal', 'protein', 'fat', 'saturates', 'carbs', 'sugar', 'salt', 'density']
    search_fields = ['name']