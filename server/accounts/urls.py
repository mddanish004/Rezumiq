from django.urls import path

from . import views

urlpatterns = [
    path("me", views.me, name="me"),
    path("me/data", views.my_data, name="me-data"),
    path("usernames/<str:username>", views.username_availability, name="username-availability"),
]
