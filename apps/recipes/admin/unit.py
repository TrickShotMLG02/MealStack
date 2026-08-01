from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.recipes.models import Unit

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'grams_per_unit', 'ml_per_unit']
    list_filter = ['type']
    search_fields = ['name']
