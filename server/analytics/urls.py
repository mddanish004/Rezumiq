from django.urls import path

from . import views

urlpatterns = [
    path("analytics", views.analytics, name="analytics"),
    path("analytics/insights", views.analytics_insights, name="analytics_insights"),
    path("analytics/views", views.analytics_views, name="analytics_views"),
]
