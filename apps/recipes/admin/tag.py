from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.recipes.models import Tag
from apps.recipes.admin.search import FuzzySearchAdminMixin

@admin.register(Tag)
class TagAdmin(FuzzySearchAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    fuzzy_search_fields = search_fields
