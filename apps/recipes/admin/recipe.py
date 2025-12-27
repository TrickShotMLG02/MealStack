import nested_admin
from django.contrib import admin
from nested_admin.nested import NestedTabularInline, NestedModelAdmin, NestedStackedInline, NestedTabularInline

from apps.recipes.models import Recipe, RecipeIngredient, RecipeStep, RecipeNutrition, RecipeTag, RecipeIngredientGroup, RecipeStepGroup


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

@admin.register(Recipe)
class RecipeAdmin(NestedModelAdmin):
    list_display = ['title', 'servings', 'status', 'source', 'author', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'source']
    inlines = [
        RecipeIngredientGroupInline,
        RecipeStepGroupInline,
        RecipeNutritionInline,
        RecipeTagsInline
    ]
