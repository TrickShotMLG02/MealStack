from django.conf import settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import Group
from apps.users.models import OIDCIdentity, OIDCProvider


class OIDCAuthBackend(OIDCAuthenticationBackend):
    def __init__(self, *args, **kwargs):
        # Database-backed providers supply their signing configuration after
        # the backend is selected. Avoid failing application startup when the
        # optional legacy global provider is only partially configured.
        algorithm = getattr(settings, "OIDC_RP_SIGN_ALGO", "HS256")
        has_key_material = getattr(settings, "OIDC_RP_IDP_SIGN_KEY", None) or getattr(settings, "OIDC_OP_JWKS_ENDPOINT", None)
        if algorithm.startswith(("RS", "ES")) and not has_key_material:
            settings.OIDC_RP_SIGN_ALGO = "HS256"
            try:
                super().__init__(*args, **kwargs)
            finally:
                settings.OIDC_RP_SIGN_ALGO = algorithm
            self.OIDC_RP_SIGN_ALGO = algorithm
        else:
            super().__init__(*args, **kwargs)

    def authenticate(self, request, **kwargs):
        self.provider = None
        if request and request.session.get("oidc_provider_slug"):
            self.provider = OIDCProvider.objects.filter(slug=request.session["oidc_provider_slug"], enabled=True).first()
            if not self.provider:
                return None
            self.OIDC_OP_TOKEN_ENDPOINT = self.provider.token_endpoint
            self.OIDC_OP_USER_ENDPOINT = self.provider.userinfo_endpoint
            self.OIDC_OP_JWKS_ENDPOINT = self.provider.jwks_endpoint or None
            self.OIDC_RP_CLIENT_ID = self.provider.client_id
            self.OIDC_RP_CLIENT_SECRET = self.provider.client_secret
            self.OIDC_RP_SIGN_ALGO = self.provider.signing_algorithm
        return super().authenticate(request, **kwargs)

    def get_or_create_user(self, access_token, id_token, payload):
        if not self.provider:
            return super().get_or_create_user(access_token, id_token, payload)
        user_info = self.get_userinfo(access_token, id_token, payload)
        if not self.verify_claims(user_info):
            return None
        subject = user_info.get("sub")
        link_user_id = self.request.session.pop("oidc_link_user_id", None)
        if link_user_id and subject:
            user = self.UserModel.objects.get(pk=link_user_id)
            OIDCIdentity.objects.update_or_create(provider=self.provider, subject=subject, defaults={"user": user})
            return user
        identity = OIDCIdentity.objects.filter(provider=self.provider, subject=subject).select_related("user").first() if subject else None
        users = [identity.user] if identity else self.filter_users_by_claims(user_info)
        if len(users) == 1:
            return self.update_user(users[0], user_info)
        if len(users) > 1 or not self.provider.auto_create_users:
            return None
        user = self.create_user(user_info)
        if subject:
            OIDCIdentity.objects.create(provider=self.provider, subject=subject, user=user)
        return user
    def create_user(self, claims):
        # auto-create user from OIDC claims
        user = super().create_user(claims)

        # Use email as username if available
        user.username = claims.get("email", user.username)

        # TODO: sync roles/permissions from OIDC claims
        user.is_superuser = False
        user.is_staff = False

        user.email = claims.get("email", "")
        self._sync_authoritative_access(user, claims)
        user.save()
        return user

    def update_user(self, user, claims):
        user.email = claims.get("email", user.email)
        self._sync_authoritative_access(user, claims)
        user.save()
        return user

    def _sync_authoritative_access(self, user, claims):
        provider = getattr(self, "provider", None)
        if not provider or not provider.authoritative:
            return
        groups = claims.get(provider.staff_groups_claim, [])
        if isinstance(groups, str):
            groups = groups.split()
        allowed = {value.strip() for value in provider.staff_groups.split(",") if value.strip()}
        user.is_staff = bool(allowed.intersection(groups))
        user.groups.set(Group.objects.filter(name__in=groups))
