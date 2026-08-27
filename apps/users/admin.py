from django.contrib import admin
from django import forms
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _

from apps.users.models import OIDCIdentity, OIDCProvider, RecipeBookmark, RecipeList


class OIDCProviderAdminForm(forms.ModelForm):
    client_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text=_("Leave blank to keep the existing client secret."),
    )

    class Meta:
        model = OIDCProvider
        fields = "__all__"

    def clean_client_secret(self):
        secret = self.cleaned_data.get("client_secret")
        if not secret and self.instance and self.instance.pk:
            return self.instance.client_secret
        if not secret:
            raise forms.ValidationError(_("A client secret is required."))
        return secret


@admin.register(OIDCProvider)
class OIDCProviderAdmin(admin.ModelAdmin):
    form = OIDCProviderAdminForm
    list_display = ("name", "enabled", "authoritative", "auto_create_users")
    list_filter = ("enabled", "authoritative", "auto_create_users")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("callback_url", "required_scopes", "authorization_flow", "setup_instructions")
    fieldsets = (
        (None, {"fields": ("name", "slug", "image_url", "enabled")}),
        (_("OIDC client"), {"fields": ("client_id", "client_secret", "authorization_endpoint", "token_endpoint", "userinfo_endpoint", "jwks_endpoint", "issuer", "scopes", "signing_algorithm")}),
        (_("Application connection details"), {"fields": ("callback_url", "required_scopes", "authorization_flow", "setup_instructions")}),
        (_("Account policy"), {"fields": ("auto_create_users", "authoritative", "staff_groups_claim", "staff_groups")}),
    )

    def get_form(self, request, obj=None, **kwargs):
        self._admin_request = request
        return super().get_form(request, obj, **kwargs)

    @admin.display(description=_("Callback URL"))
    def callback_url(self, obj):
        try:
            callback_path = reverse("oidc_authentication_callback")
        except NoReverseMatch:
            callback_path = "/oidc/callback/"
        request = getattr(self, "_admin_request", None)
        return request.build_absolute_uri(callback_path) if request else callback_path

    @admin.display(description=_("Required scopes"))
    def required_scopes(self, obj):
        return obj.scopes or "openid email profile"

    @admin.display(description=_("Authorization flow"))
    def authorization_flow(self, obj):
        return _("Authorization Code")

    @admin.display(description=_("Setup instructions"))
    def setup_instructions(self, obj):
        return _("Register the callback URL and enable the required scopes in your identity provider. Use the client ID and secret generated there in the OIDC client section.")


@admin.register(OIDCIdentity)
class OIDCIdentityAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "subject", "created_at")
    list_filter = ("provider",)
    search_fields = ("user__username", "user__email", "provider__name", "subject")


admin.site.register(RecipeBookmark)
admin.site.register(RecipeList)
