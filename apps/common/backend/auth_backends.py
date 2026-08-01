from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class OIDCAuthBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        # auto-create user from OIDC claims
        user = super().create_user(claims)

        # Use email as username if available
        user.username = claims.get("email", user.username)

        # TODO: sync roles/permissions from OIDC claims
        user.is_superuser = False
        user.is_staff = False

        user.email = claims.get("email", "")
        user.save()
        return user

    def update_user(self, user, claims):
        user.email = claims.get("email", user.email)
        # TODO: sync roles/permissions from OIDC claims
        user.save()
        return user
