from django.contrib import admin
from apps.recipes.models import Cuisine


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']