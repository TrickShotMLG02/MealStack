from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.recipes.models import Cuisine
from apps.recipes.admin.search import FuzzySearchAdminMixin


@admin.register(Cuisine)
class CuisineAdmin(FuzzySearchAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    fuzzy_search_fields = search_fields
