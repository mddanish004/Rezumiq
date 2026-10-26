from django.urls import path

from . import views

urlpatterns = [
    path("resumes/<uuid:resume_id>/pdf", views.resume_pdf, name="resume_pdf"),
    path("resumes/<uuid:resume_id>/tex", views.resume_tex, name="resume_tex"),
    path(
        "resumes/<uuid:resume_id>/json-resume", views.resume_json_resume, name="resume_json_resume"
    ),
    path("previews", views.previews, name="previews"),
]
