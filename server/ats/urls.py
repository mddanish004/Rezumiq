"""ATS routes."""

from django.urls import path

from . import views

urlpatterns = [
    path("resumes/<uuid:resume_id>/ats-reports", views.resume_ats_report, name="resume_ats_report"),
    path("ats-reports", views.public_ats_report, name="public_ats_report"),
    path("ats-reviews", views.ats_review, name="ats_review"),
]
