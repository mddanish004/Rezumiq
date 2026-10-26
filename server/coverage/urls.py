from django.urls import path

from . import views

urlpatterns = [
    path("resumes/<uuid:resume_id>/coverage", views.coverage, name="coverage"),
]
