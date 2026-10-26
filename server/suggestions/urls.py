from django.urls import path

from . import views

urlpatterns = [
    path("resumes/<uuid:resume_id>/suggestions", views.suggestions, name="suggestions"),
    path(
        "resumes/<uuid:resume_id>/suggestions/<uuid:suggestion_id>",
        views.suggestion_detail,
        name="suggestion_detail",
    ),
    path(
        "resumes/<uuid:resume_id>/suggestions/<uuid:suggestion_id>/apply",
        views.apply_suggestion,
        name="apply_suggestion",
    ),
]
