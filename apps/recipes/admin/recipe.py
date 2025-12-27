from django.contrib import admin
from django.utils.html import format_html
from nested_admin.nested import NestedTabularInline, NestedModelAdmin, NestedStackedInline, NestedTabularInline

from apps.recipes.models import Recipe, RecipeIngredient, RecipeStep, RecipeNutrition, RecipeTag, RecipeIngredientGroup, RecipeStepGroup, RecipeNote, RecipeImage, Cuisine


# Nested Inline for ingredients
class RecipeIngredientInline(NestedTabularInline):
    model = RecipeIngredient
    extra = 1
    fk_name = 'group'
    autocomplete_fields = ['ingredient', 'unit']
    fields = ['ingredient', 'quantity', 'unit', 'order']

# Nested Ingredient group inline
class RecipeIngredientGroupInline(NestedTabularInline):
    model = RecipeIngredientGroup
    inlines = [RecipeIngredientInline]
    extra = 1
    #fields = ['name', 'order']

# Inline for steps
class RecipeStepInline(NestedTabularInline):
    model = RecipeStep
    extra = 1

# Nested Step group inline
class RecipeStepGroupInline(NestedTabularInline):
    model = RecipeStepGroup
    inlines = [RecipeStepInline]
    extra = 1
    #fields = ['name', 'order']

# Inline for nutrition (read-only)
class RecipeNutritionInline(NestedTabularInline):
    model = RecipeNutrition
    can_delete = False
    readonly_fields = [
        'total_kcal', 'total_protein', 'total_fat', 'total_carbs', 'total_salt',
        'per_serving_kcal', 'per_serving_protein', 'per_serving_fat', 'per_serving_carbs', 'per_serving_salt'
    ]
    max_num = 1
    extra = 0

# Inline for tags
class RecipeTagsInline(NestedTabularInline):
    model = RecipeTag
    extra = 1

# Inline for notes
class RecipeNotesInline(NestedTabularInline):
    model = RecipeNote
    extra = 1

class RecipeImageInline(NestedTabularInline):
    model = RecipeImage
    extra = 0
    readonly_fields = ("preview",)

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


    list_display = ['title', 'primary_image_preview', 'servings', 'preparation_time', 'cooking_time', 'resting_time', 'total_time_display', 'author', 'created_at', 'updated_at', 'status']
    list_filter = ['status', 'created_at', 'cuisine',]
    search_fields = ['title', 'source',]
    inlines = [
        RecipeImageInline,
        RecipeIngredientGroupInline,
        RecipeStepGroupInline,
        RecipeNotesInline,
        RecipeNutritionInline,
        RecipeTagsInline,
    ]
