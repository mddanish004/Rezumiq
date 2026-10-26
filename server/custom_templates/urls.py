from django.urls import path

from . import views

urlpatterns = [
    path("custom-templates", views.custom_templates, name="custom_templates"),
    path(
        "custom-templates/<uuid:custom_template_id>",
        views.custom_template_detail,
        name="custom_template",
    ),
]
