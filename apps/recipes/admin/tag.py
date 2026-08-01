from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.recipes.models import Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
