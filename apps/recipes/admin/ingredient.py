from django.contrib import admin
from apps.recipes.models import Ingredient

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'kcal', 'protein', 'fat', 'carbs', 'salt', 'density']
    search_fields = ['name']