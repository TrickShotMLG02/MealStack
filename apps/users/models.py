from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class OIDCProvider(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("Slug"))
    image_url = models.URLField(blank=True, verbose_name=_("Image URL"))
    client_id = models.CharField(max_length=255, verbose_name=_("Client ID"))
    client_secret = models.CharField(max_length=500, verbose_name=_("Client secret"))
    authorization_endpoint = models.URLField(verbose_name=_("Authorization endpoint"))
    token_endpoint = models.URLField(verbose_name=_("Token endpoint"))
    userinfo_endpoint = models.URLField(verbose_name=_("User info endpoint"))
    jwks_endpoint = models.URLField(blank=True, verbose_name=_("JWKS endpoint"))
    issuer = models.URLField(blank=True, verbose_name=_("Issuer"))
    scopes = models.CharField(max_length=255, default="openid email profile", verbose_name=_("Scopes"))
    signing_algorithm = models.CharField(max_length=20, default="RS256", verbose_name=_("Signing algorithm"))
    enabled = models.BooleanField(default=True, verbose_name=_("Enabled"))
    authoritative = models.BooleanField(default=False, verbose_name=_("Authoritative"))
    auto_create_users = models.BooleanField(default=True, verbose_name=_("Auto-create users"))
    staff_groups_claim = models.CharField(max_length=100, default="groups", blank=True, verbose_name=_("Staff groups claim"))
    staff_groups = models.CharField(max_length=500, default="", blank=True, help_text=_("Groups that grant staff access, separated by commas."))

    class Meta:
        ordering = ["name"]
        verbose_name = _("OIDC provider")
        verbose_name_plural = _("OIDC providers")

    def __str__(self):
        return self.name


class OIDCIdentity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oidc_identities", verbose_name=_("User"))
    provider = models.ForeignKey(OIDCProvider, on_delete=models.CASCADE, related_name="identities", verbose_name=_("Provider"))
    subject = models.CharField(max_length=255, verbose_name=_("Subject"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    class Meta:
        constraints = [models.UniqueConstraint(fields=["provider", "subject"], name="unique_oidc_provider_subject")]
        verbose_name = _("OIDC identity")
        verbose_name_plural = _("OIDC identities")


class RecipeBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_bookmarks")
    recipe = models.ForeignKey("recipes.Recipe", on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "recipe"], name="unique_user_recipe_bookmark")]
        verbose_name = _("Recipe bookmark")
        verbose_name_plural = _("Recipe bookmarks")


class RecipeList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_lists")
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    recipes = models.ManyToManyField("recipes.Recipe", related_name="user_lists", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_user_recipe_list_name")]
        verbose_name = _("Recipe list")
        verbose_name_plural = _("Recipe lists")

    def __str__(self):
        return self.name
