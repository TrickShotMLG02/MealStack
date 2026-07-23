from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class OIDCAuthBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        # auto-create user from OIDC claims
        user = super().create_user(claims)

        # Use email as username if available
        user.username = claims.get("email", user.username)

        # Give admin access
        # TODO: sync roles/permissions from OIDC
        user.is_staff = True
        user.is_superuser = False

        user.email = claims.get("email", "")
        user.save()
        return user

    def update_user(self, user, claims):
        # Update email if it changes
        user.email = claims.get("email", user.email)
        user.save()
        return user