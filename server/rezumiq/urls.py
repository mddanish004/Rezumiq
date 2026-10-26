from django.contrib import admin
from django.urls import include, path

from accounts import views
from api.common.errors import internal_error, not_found

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    path("auth/guest", views.guest_login, name="guest-login"),
    path("health", views.health, name="health"),
    path("health/deep", views.health_deep, name="health-deep"),
    path("v1/", include("accounts.urls")),
    path("v1/", include("resumes.urls")),
    path("v1/", include("uploads.urls")),
    path("v1/", include("pdfs.urls")),
    path("v1/", include("custom_templates.urls")),
    path("v1/", include("jobs.urls")),
    path("v1/", include("share_links.urls")),
    path("v1/", include("public.urls")),
    path("v1/", include("coverage.urls")),
    path("v1/", include("analytics.urls")),
    path("v1/", include("promo_codes.urls")),
    path("v1/", include("suggestions.urls")),
    path("v1/", include("ai_keys.urls")),
    path("v1/", include("ai.urls")),
    path("v1/", include("imports.urls")),
    path("v1/", include("billing.urls")),
    path("v1/", include("usage.urls")),
    path("v1/", include("admin.urls")),
    path("v1/", include("ats.urls")),
]

handler404 = not_found
handler500 = internal_error
