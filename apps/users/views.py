from django.conf import settings
from django.db.models import Prefetch, Q
from django.templatetags.static import static
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.crypto import get_random_string
from urllib.parse import urlencode
from mozilla_django_oidc.utils import (
    add_state_and_verifier_and_nonce_to_session,
    absolutify,
    generate_code_challenge,
)

from apps.recipes.models import Recipe, RecipeImage
from apps.users.forms import ProfileForm, ProfilePasswordForm, RecipeListForm
from apps.users.models import OIDCIdentity, OIDCProvider, RecipeBookmark, RecipeList


def _safe_post_redirect(request, fallback):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback


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
        "oidc_providers": OIDCProvider.objects.filter(Q(enabled=True) | Q(identities__user=request.user)).distinct(),
        "linked_oidc_provider_ids": set(OIDCIdentity.objects.filter(user=request.user).values_list("provider_id", flat=True)),
    })


@login_required
def toggle_bookmark(request, slug):
    if request.method != "POST":
        return redirect("recipes:recipe_detail", slug=slug)
    recipe = get_object_or_404(Recipe, slug=slug, status="published")
    bookmark, created = RecipeBookmark.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        bookmark.delete()
    return redirect(_safe_post_redirect(request, f"/recipes/{slug}/"))


@login_required
def add_to_list(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, status="published")
    if request.method == "POST":
        recipe_list = get_object_or_404(RecipeList, pk=request.POST.get("list_id"), user=request.user)
        recipe_list.recipes.add(recipe)
        messages.success(request, _("Recipe added to your list."))
    return redirect(_safe_post_redirect(request, f"/recipes/{slug}/"))


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
    return redirect(_safe_post_redirect(request, f"/recipes/{slug}/"))


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


class AccountLoginView(LoginView):
    template_name = "users/login.html"

    def get_success_url(self):
        return self.get_redirect_url() or reverse("users:profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "local_login_enabled": not settings.OIDC_ENABLED or settings.OIDC_ALLOW_LOCAL_LOGIN,
            "oidc_enabled": settings.OIDC_ENABLED,
            "oidc_providers": OIDCProvider.objects.filter(enabled=True),
        })
        return context


def oidc_login(request, slug):
    provider = get_object_or_404(OIDCProvider, slug=slug, enabled=True)
    state = get_random_string(32)
    nonce = get_random_string(32)
    try:
        callback = reverse("oidc_authentication_callback")
    except NoReverseMatch:
        callback = "/oidc/callback/"
    params = {
        "response_type": "code",
        "scope": provider.scopes,
        "client_id": provider.client_id,
        "redirect_uri": absolutify(request, callback),
        "state": state,
        "nonce": nonce,
    }
    code_verifier = get_random_string(64)
    params["code_challenge"] = generate_code_challenge(code_verifier, "S256")
    params["code_challenge_method"] = "S256"
    add_state_and_verifier_and_nonce_to_session(request, state, params, code_verifier)
    request.session["oidc_provider_slug"] = provider.slug
    if request.user.is_authenticated and request.GET.get("link") == "1":
        request.session["oidc_link_user_id"] = request.user.pk
    next_url = request.GET.get("next")
    request.session["oidc_login_next"] = (
        next_url
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        else None
    )
    return HttpResponseRedirect(f"{provider.authorization_endpoint}?{urlencode(params)}")


@login_required
def oidc_unlink(request, slug):
    if request.method == "POST":
        identity = get_object_or_404(OIDCIdentity, provider__slug=slug, user=request.user)
        if request.user.oidc_identities.count() <= 1:
            messages.error(request, _("You cannot remove your only OIDC connection."))
        else:
            identity.delete()
            messages.success(request, _("OIDC provider unlinked."))
    return redirect("users:profile")
