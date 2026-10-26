from django.urls import path

from . import views

urlpatterns = [
    path("jobs", views.jobs, name="jobs"),
    path("jobs/<uuid:job_id>", views.job_detail, name="job"),
]
