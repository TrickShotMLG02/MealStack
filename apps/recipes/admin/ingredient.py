from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.recipes.models import Ingredient

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'kcal', 'protein', 'fat', 'saturates', 'carbs', 'sugar', 'salt', 'density']
    search_fields = ['name']