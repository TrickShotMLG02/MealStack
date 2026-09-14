from django.urls import path

from apps.users import views

app_name = "users"

urlpatterns = [
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("profile/", views.profile, name="profile"),
    path("bookmark/<slug:slug>/", views.toggle_bookmark, name="toggle_bookmark"),
    path("list/<slug:slug>/add/", views.add_to_list, name="add_to_list"),
    path("list/<int:pk>/", views.recipe_list_detail, name="recipe_list_detail"),
    path("list/<int:pk>/remove/<slug:slug>/", views.remove_from_list, name="remove_from_list"),
    path("list/<int:pk>/delete/", views.delete_recipe_list, name="delete_recipe_list"),
    path("lists/update/<slug:slug>/", views.update_recipe_lists, name="update_recipe_lists"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("oidc/<slug:slug>/login/", views.oidc_login, name="oidc_login"),
    path("oidc/<slug:slug>/unlink/", views.oidc_unlink, name="oidc_unlink"),
]
