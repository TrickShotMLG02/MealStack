from django.contrib import admin
from apps.recipes.models import Recipe, RecipeIngredient, RecipeStep, RecipeNutrition


# Inline for ingredients
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

# Inline for steps
class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1

# Inline for nutrition (read-only)
class RecipeNutritionInline(admin.StackedInline):
    model = RecipeNutrition
    can_delete = False
    readonly_fields = [
        'total_kcal', 'total_protein', 'total_fat', 'total_carbs', 'total_salt',
        'per_serving_kcal', 'per_serving_protein', 'per_serving_fat', 'per_serving_carbs', 'per_serving_salt'
    ]
    max_num = 1
    extra = 0

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'servings', 'status', 'source', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'source']
    inlines = [RecipeIngredientInline, RecipeStepInline, RecipeNutritionInline]
