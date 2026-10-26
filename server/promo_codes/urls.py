from django.urls import path

from . import views

urlpatterns = [
    path("promo-redemptions", views.redeem, name="promo_redeem"),
]
