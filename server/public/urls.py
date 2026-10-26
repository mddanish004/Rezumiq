from django.urls import path

from . import views

urlpatterns = [
    path("public/users/<str:username>", views.public_profile, name="public_profile"),
    path(
        "public/users/<str:username>/resumes/<str:slug>", views.public_resume, name="public_resume"
    ),
    path(
        "public/users/<str:username>/resumes/<str:slug>/pdf",
        views.public_resume_pdf,
        name="public_resume_pdf",
    ),
]
