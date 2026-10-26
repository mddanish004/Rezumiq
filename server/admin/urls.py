from django.urls import path

from . import views

urlpatterns = [
    path("admin/overview", views.overview, name="admin-overview"),
    path("admin/users", views.users, name="admin-users"),
    path("admin/users/<str:user_id>", views.user_detail, name="admin-user"),
    path("admin/users/<str:user_id>/sessions", views.revoke_sessions, name="admin-user-sessions"),
    path("admin/users/<str:user_id>/usage", views.reset_usage, name="admin-user-usage"),
    path(
        "admin/users/<str:user_id>/subscriptions",
        views.grant_subscription,
        name="admin-user-subscriptions",
    ),
    path(
        "admin/users/<str:user_id>/subscriptions/<str:subscription_id>",
        views.revoke_subscription,
        name="admin-user-subscription",
    ),
    path("admin/ai", views.ai_usage, name="admin-ai"),
    path("admin/revenue", views.revenue, name="admin-revenue"),
    path("admin/content", views.content, name="admin-content"),
    path("admin/traffic", views.traffic, name="admin-traffic"),
    path("admin/system", views.system, name="admin-system"),
]
