from django.urls import path

from . import views

urlpatterns = [
    path("checkouts", views.checkouts, name="checkouts"),
    path("subscription", views.subscription, name="subscription"),
    path("refunds/quote", views.refund_quote, name="refund-quote"),
    path("refunds", views.refunds, name="refunds"),
    path("webhooks/dodo", views.dodo_webhook, name="dodo-webhook"),
]
