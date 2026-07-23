from django.urls import path
from apps.recipes import views

app_name = 'recipes'

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),  # /recipes/
    path('search-suggestions/', views.recipe_search_suggestions, name='recipe_search_suggestions'),
    path("<slug:slug>/", views.recipe_detail, name="recipe_detail"),
    path("<slug:slug>/export.pdf", views.recipe_export_pdf, name="recipe_export_pdf"),
]
