from django.urls import path

from . import views

urlpatterns = [
    path("uploads", views.uploads, name="uploads"),
    path("uploads/<uuid:upload_id>", views.upload_detail, name="upload"),
]
