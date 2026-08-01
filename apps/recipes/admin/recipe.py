from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from apps.recipes.models import (
    Recipe,
    RecipeIngredient,
    RecipeStep,
    RecipeNutrition,
    RecipeTag,
    RecipeIngredientGroup,
    RecipeStepGroup,
    RecipeNote,
    RecipeImage,
    Cuisine,
)
from apps.recipes.services.nutrition import update_recipe_nutrition


class RecipeIngredientInline(NestedTabularInline):
    model = RecipeIngredient
    fk_name = 'group'
    extra = 1
    autocomplete_fields = ['ingredient', 'unit']
    fields = ['ingredient', 'quantity', 'unit', 'order']
    ordering = ['order']

class RecipeIngredientGroupInline(NestedStackedInline):
    model = RecipeIngredientGroup
    inlines = [RecipeIngredientInline]
    extra = 1
    fields = ['name', 'order']
    ordering = ['order']

class RecipeStepInline(NestedTabularInline):
    model = RecipeStep
    extra = 1
    fields = ['order', 'description']
    ordering = ['order']

class RecipeStepGroupInline(NestedStackedInline):
    model = RecipeStepGroup
    inlines = [RecipeStepInline]
    extra = 1
    fields = ['name', 'order']
    ordering = ['order']

class RecipeNutritionInline(NestedTabularInline):
    model = RecipeNutrition
    can_delete = False
    readonly_fields = [
        'total_kcal', 'total_protein', 'total_fat', 'total_carbs', 'total_saturates', 'total_sugar', 'total_salt',
        'per_serving_kcal', 'per_serving_protein', 'per_serving_fat', 'per_serving_carbs', 'per_serving_saturates', 'per_serving_sugar', 'per_serving_salt'
    ]
    max_num = 1
    extra = 0
    verbose_name_plural = "Nutrition"
    classes = ("collapse",)

class RecipeTagsInline(NestedTabularInline):
    model = RecipeTag
    extra = 1
    classes = ("collapse",)

class RecipeNotesInline(NestedTabularInline):
    model = RecipeNote
    extra = 1
    classes = ("collapse",)

class RecipeImageInline(NestedTabularInline):
    model = RecipeImage
    extra = 0
    readonly_fields = ("preview",)
    classes = ("collapse",)

    fields = ("preview", "image", "caption", "is_primary", "ordering")

    def preview(self, obj):
        if not obj.image:
            return "-"
        return format_html(
            '<img src="{}" style="height: 100px; object-fit: contain;" />',
            obj.image.url,
        )

@admin.register(Recipe)
class RecipeAdmin(NestedModelAdmin):
    save_on_top = True
    autocomplete_fields = ["cuisine"]
    actions = ["mark_as_published", "mark_as_draft"]
    list_display = [
        'title',
        'primary_image_preview',
        'servings',
        'preparation_time',
        'cooking_time',
        'resting_time',
        'total_time_display',
        'author',
        'created_at',
        'updated_at',
        'status',
    ]
    list_filter = ['status', 'created_at', 'cuisine']
    search_fields = ['title', 'source', 'author']
    fieldsets = (
        (
            "Recipe",
            {
                "fields": (
                    "title",
                    "slug",
                    "status",
                    "servings",
                    "cuisine",
                    "author",
                    "source",
                ),
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    ("preparation_time", "cooking_time", "resting_time"),
                ),
            },
        ),
    )

    def primary_image_preview(self, obj):
        """
        Returns the primary image for this recipe, or '-' if none.
        """
        # 'images' is the related_name on RecipeImage.foreignkey
        primary_image = obj.recipeimage_set.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="height:50px; object-fit:contain;" />',
                primary_image.image.url
            )
        return "-"

    primary_image_preview.short_description = "Primary Image"

    inlines = [
        RecipeImageInline,
        RecipeIngredientGroupInline,
        RecipeStepGroupInline,
        RecipeNotesInline,
        RecipeNutritionInline,
        RecipeTagsInline,
    ]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        update_recipe_nutrition(form.instance)

    @admin.action(description=_("Mark selected recipes as published"))
    def mark_as_published(self, request, queryset):
        updated = queryset.update(status="published")
        self.message_user(request, _("Published %(count)d recipe(s).") % {"count": updated})

    @admin.action(description=_("Mark selected recipes as draft"))
    def mark_as_draft(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, _("Moved %(count)d recipe(s) to draft.") % {"count": updated})
