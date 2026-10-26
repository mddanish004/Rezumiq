from django.urls import path

from . import views

urlpatterns = [
    path("me/ai-runs", views.ai_runs, name="ai-runs"),
]
