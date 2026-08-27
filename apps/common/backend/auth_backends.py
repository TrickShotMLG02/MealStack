from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError, transaction
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import jwt
from django.contrib.auth.models import Group
from apps.users.models import OIDCIdentity, OIDCProvider


OIDC_SIGNING_ALGORITHMS = {
    "RS256", "RS384", "RS512",
    "PS256", "PS384", "PS512",
    "ES256", "ES384", "ES512",
    "HS256", "HS384", "HS512",
}


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
            self.OIDC_RP_IDP_SIGN_KEY = None
            self.OIDC_RP_CLIENT_ID = self.provider.client_id
            self.OIDC_RP_CLIENT_SECRET = self.provider.client_secret
            self.OIDC_RP_SIGN_ALGO = self.provider.signing_algorithm
            self.OIDC_OP_ISSUER = self.provider.issuer
        return super().authenticate(request, **kwargs)

    def _verify_jws(self, payload, key):
        """Verify an OIDC JWT, including its issuer and intended audience."""
        if not self.provider:
            return super()._verify_jws(payload, key)

        algorithm = self.provider.signing_algorithm
        if algorithm not in OIDC_SIGNING_ALGORITHMS:
            raise SuspiciousOperation("Unsupported OIDC signing algorithm.")
        if not self.provider.issuer:
            raise SuspiciousOperation("OIDC provider issuer is not configured.")

        try:
            header = jwt.get_unverified_header(payload)
            if header.get("alg") != algorithm:
                raise SuspiciousOperation("OIDC token algorithm mismatch.")

            claims = jwt.decode(
                payload,
                key,
                algorithms=[algorithm],
                audience=self.provider.client_id,
                issuer=self.provider.issuer,
                leeway=getattr(settings, "OIDC_LEEWAY", 0),
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except SuspiciousOperation:
            raise
        except jwt.PyJWTError as exc:
            raise SuspiciousOperation("OIDC token validation failed.") from exc

        audience = claims.get("aud")
        if isinstance(audience, list) and len(audience) > 1 and claims.get("azp") != self.provider.client_id:
            raise SuspiciousOperation("OIDC authorized party validation failed.")
        if "azp" in claims and claims["azp"] != self.provider.client_id:
            raise SuspiciousOperation("OIDC authorized party validation failed.")
        return claims

    def get_or_create_user(self, access_token, id_token, payload):
        if not self.provider:
            return super().get_or_create_user(access_token, id_token, payload)
        user_info = self.get_userinfo(access_token, id_token, payload)
        if not self.verify_claims(user_info):
            return None
        subject = user_info.get("sub")
        if subject != payload.get("sub"):
            return None
        link_user_id = self.request.session.pop("oidc_link_user_id", None)
        if link_user_id:
            request_user = getattr(self.request, "user", None)
            if not request_user or not request_user.is_authenticated or request_user.pk != link_user_id:
                return None
            user = self.UserModel.objects.get(pk=link_user_id)
            identity = OIDCIdentity.objects.filter(provider=self.provider, subject=subject).first()
            if identity and identity.user_id != user.pk:
                return None
            if not identity:
                try:
                    with transaction.atomic():
                        OIDCIdentity.objects.create(provider=self.provider, subject=subject, user=user)
                except IntegrityError:
                    return None
            return user

        # Normal login is identity-only. A provider must have been explicitly
        # linked from the user's profile before it can authenticate that user.
        identity = OIDCIdentity.objects.filter(
            provider=self.provider, subject=subject
        ).select_related("user").first()
        if not identity:
            return None
        return self.update_user(identity.user, user_info)

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
        user.groups.set(Group.objects.filter(name__in=allowed.intersection(groups)))

    def verify_claims(self, claims):
        """Require stable OIDC identity claims and verified email addresses."""
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            return False
        if claims.get("email") and claims.get("email_verified") is not True:
            return False
        return True
