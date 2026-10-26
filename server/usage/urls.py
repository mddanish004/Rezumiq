from django.urls import path

from . import views

urlpatterns = [
    path("usage", views.usage, name="usage"),
]
