from django.conf import settings
from django.contrib.auth.views import LoginView


class CustomAdminLoginView(LoginView):
    """
    Overrides the admin login page to show OIDC button and optionally username/password form.
    """
    template_name = "admin/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['OIDC_ENABLED'] = getattr(settings, "OIDC_ENABLED")
        context['OIDC_ALLOW_LOCAL_LOGIN'] = getattr(settings, "OIDC_ALLOW_LOCAL_LOGIN")
        return context
