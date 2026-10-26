from django.urls import path

from . import views

urlpatterns = [
    path("me/ai-keys", views.ai_keys, name="ai_keys"),
    path("me/ai-keys/<str:provider>/models", views.ai_key_models, name="ai_key_models"),
    path("me/ai-keys/<str:provider>", views.ai_key_detail, name="ai_key_detail"),
]
