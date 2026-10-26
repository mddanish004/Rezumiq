from django.urls import path

from . import views

urlpatterns = [
    path("profile", views.profile, name="profile"),
    path("templates", views.templates_list, name="templates"),
    path("resumes", views.resumes, name="resumes"),
    path("resumes/<uuid:resume_id>", views.resume_detail, name="resume"),
    path("resumes/<uuid:resume_id>/versions", views.versions, name="versions"),
    path(
        "resumes/<uuid:resume_id>/versions/<uuid:version_id>", views.version_detail, name="version"
    ),
]
