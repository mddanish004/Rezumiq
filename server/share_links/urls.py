from django.urls import path

from . import views

urlpatterns = [
    path(
        "resumes/<uuid:resume_id>/share-links",
        views.share_links_for_resume,
        name="share_links_for_resume",
    ),
    path("share-links/<uuid:share_link_id>", views.share_link_detail, name="share_link_detail"),
    path("share-links/<uuid:share_link_id>/stats", views.share_link_stats, name="share_link_stats"),
]
