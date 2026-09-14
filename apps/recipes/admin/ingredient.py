from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.recipes.models import Ingredient
from apps.recipes.admin.search import FuzzySearchAdminMixin

@admin.register(Ingredient)
class IngredientAdmin(FuzzySearchAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'kcal', 'protein', 'fat', 'saturates', 'carbs', 'sugar', 'salt', 'density']
    search_fields = ['name', 'generic_name', 'brand', 'ean']
    fuzzy_search_fields = search_fields
