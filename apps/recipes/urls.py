from django.urls import path
from apps.recipes import views

app_name = 'recipes'

urlpatterns = [
    path("<slug:slug>/", views.recipe_detail, name="detail"),
]