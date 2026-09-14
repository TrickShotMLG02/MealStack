"""
URL configuration for MealStack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView

from apps.recipes import views
from apps.recipes.admin import *


urlpatterns = [
    path("", RedirectView.as_view(url="/recipes/", permanent=False)),
    path("admin/login/", views.CustomAdminLoginView.as_view(), name="admin_login"),
    path('admin/', my_admin_site.urls),
    #path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),
    path('recipes/', include('apps.recipes.urls', namespace='recipes')),
    path('account/', include('apps.users.urls', namespace='users')),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.OIDC_ENABLED:
    urlpatterns += [
        path("oidc/", include("mozilla_django_oidc.urls")),
    ]

# TODO: Only for DEV Environment
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
