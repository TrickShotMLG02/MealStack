from mozilla_django_oidc.views import OIDCAuthenticationCallbackView


class MealStackOIDCCallbackView(OIDCAuthenticationCallbackView):
    """Clean all provider/linking state after every callback attempt."""

    @property
    def success_url(self):
        next_url = self.request.session.get("oidc_login_next", None)
        if next_url and next_url.startswith("/admin/") and not self.user.is_staff:
            return "/recipes/"
        return super().success_url

    def get(self, request):
        try:
            return super().get(request)
        finally:
            for key in ("oidc_provider_slug", "oidc_link_user_id", "oidc_login_next", "oidc_states"):
                request.session.pop(key, None)
            request.session.save()
