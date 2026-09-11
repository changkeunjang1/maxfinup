from django.urls import path

from . import views

app_name = "ledger"

urlpatterns = [
    path("", views.home, name="home"),
    path("designs/", views.design_previews, name="designs"),
    path("trends/", views.trends, name="trends"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms, name="terms"),
    path("email-collection-refusal/", views.email_refusal, name="email_refusal"),
    path("chapter/<slug:slug>/", views.chapter_detail, name="chapter"),
]
