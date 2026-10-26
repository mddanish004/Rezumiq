from django.urls import path

from . import views

urlpatterns = [
    path("imports", views.imports, name="imports"),
    path("resume-drafts", views.resume_drafts, name="resume-drafts"),
]
