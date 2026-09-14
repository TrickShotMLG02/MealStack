from mozilla_django_oidc.views import OIDCAuthenticationCallbackView


class MealStackOIDCCallbackView(OIDCAuthenticationCallbackView):
    """Clean all provider/linking state after every callback attempt."""

    def get(self, request):
        try:
            return super().get(request)
        finally:
            for key in ("oidc_provider_slug", "oidc_link_user_id", "oidc_login_next", "oidc_states"):
                request.session.pop(key, None)
            request.session.save()
