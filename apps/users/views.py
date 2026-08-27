from django.conf import settings
from django.db.models import Prefetch
from django.templatetags.static import static
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from apps.recipes.models import Recipe, RecipeImage
from apps.users.forms import ProfileForm, ProfilePasswordForm, RecipeListForm
from apps.users.models import RecipeBookmark, RecipeList


@login_required
def profile(request):
    profile_form = ProfileForm(instance=request.user)
    password_form = ProfilePasswordForm(request.user)
    list_form = RecipeListForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Your profile was updated."))
                return redirect("users:profile")
        elif action == "password":
            password_form = ProfilePasswordForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("Your password was changed."))
                return redirect("users:profile")
        elif action == "list":
            list_form = RecipeListForm(request.POST)
            if list_form.is_valid():
                if RecipeList.objects.filter(user=request.user, name=list_form.cleaned_data["name"]).exists():
                    list_form.add_error("name", _("You already have a list with this name."))
                else:
                    recipe_list = list_form.save(commit=False)
                    recipe_list.user = request.user
                    recipe_list.save()
                    messages.success(request, _("Your recipe list was created."))
                    return redirect("users:profile")

    return render(request, "users/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
        "list_form": list_form,
        "bookmarks": RecipeBookmark.objects.filter(user=request.user).select_related("recipe"),
        "recipe_lists": RecipeList.objects.filter(user=request.user).prefetch_related("recipes"),
        "oidc_enabled": settings.OIDC_ENABLED,
    })


@login_required
def toggle_bookmark(request, slug):
    if request.method != "POST":
        return redirect("recipes:recipe_detail", slug=slug)
    recipe = get_object_or_404(Recipe, slug=slug, status="published")
    bookmark, created = RecipeBookmark.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        bookmark.delete()
    return redirect(request.POST.get("next") or f"/recipes/{slug}/")


@login_required
def add_to_list(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, status="published")
    if request.method == "POST":
        recipe_list = get_object_or_404(RecipeList, pk=request.POST.get("list_id"), user=request.user)
        recipe_list.recipes.add(recipe)
        messages.success(request, _("Recipe added to your list."))
    return redirect(request.POST.get("next") or f"/recipes/{slug}/")


@login_required
def update_recipe_lists(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, status="published")
    if request.method == "POST":
        new_list_name = (request.POST.get("new_list_name") or "").strip()
        selected_ids = set(request.POST.getlist("list_ids"))
        if new_list_name:
            recipe_list, created = RecipeList.objects.get_or_create(user=request.user, name=new_list_name)
            selected_ids.add(str(recipe_list.pk))
            if created:
                recipe_list.recipes.add(recipe)
                messages.success(request, _("New list created and recipe added."))
            else:
                messages.info(request, _("A list with this name already exists."))
        user_lists = RecipeList.objects.filter(user=request.user)
        for recipe_list in user_lists:
            if str(recipe_list.pk) in selected_ids:
                recipe_list.recipes.add(recipe)
            else:
                recipe_list.recipes.remove(recipe)
        messages.success(request, _("Your recipe lists were updated."))
    return redirect(request.POST.get("next") or f"/recipes/{slug}/")


@login_required
def recipe_list_detail(request, pk):
    recipe_list = get_object_or_404(
        RecipeList.objects.prefetch_related(
            Prefetch(
                "recipes",
                queryset=Recipe.objects.select_related("cuisine").prefetch_related(
                    Prefetch("recipeimage_set", queryset=RecipeImage.objects.all().order_by("-is_primary", "ordering"), to_attr="images")
                ),
            )
        ),
        pk=pk,
        user=request.user,
    )
    bookmarked_ids = set(RecipeBookmark.objects.filter(user=request.user, recipe_id__in=recipe_list.recipes.values_list("pk", flat=True)).values_list("recipe_id", flat=True))
    for recipe in recipe_list.recipes.all():
        recipe.is_bookmarked = recipe.pk in bookmarked_ids
        primary_image = next((image for image in getattr(recipe, "images", []) if image.is_primary and image.image), None)
        recipe.list_image_url = primary_image.image.url if primary_image else static("recipes/images/placeholder.jpg")
    return render(request, "users/recipe_list_detail.html", {"recipe_list": recipe_list})


@login_required
def remove_from_list(request, pk, slug):
    recipe_list = get_object_or_404(RecipeList, pk=pk, user=request.user)
    recipe = get_object_or_404(Recipe, slug=slug)
    if request.method == "POST":
        recipe_list.recipes.remove(recipe)
        messages.success(request, _("Recipe removed from your list."))
    return redirect("users:recipe_list_detail", pk=recipe_list.pk)


@login_required
def delete_recipe_list(request, pk):
    recipe_list = get_object_or_404(RecipeList, pk=pk, user=request.user)
    if request.method == "POST":
        if recipe_list.recipes.exists():
            messages.error(request, _("Lists containing recipes cannot be deleted."))
        else:
            recipe_list.delete()
            messages.success(request, _("Your recipe list was deleted."))
    return redirect("users:profile")


class UserLogoutView(LogoutView):
    next_page = "/recipes/"
