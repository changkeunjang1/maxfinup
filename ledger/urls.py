from django.urls import path

from . import views

app_name = "ledger"

urlpatterns = [
    path("", views.home, name="home"),
    path("designs/", views.design_previews, name="designs"),
    path("trends/", views.trends, name="trends"),
    path("asset-management/", views.asset_management, name="asset_management"),
    path("asset-management/api/assets/", views.asset_api_list, name="asset_api_list"),
    path("asset-management/api/assets/<int:pk>/", views.asset_api_detail, name="asset_api_detail"),
    path("experts/", views.experts, name="experts"),
    path("experts/<slug:slug>/", views.asset_topic, name="asset_topic"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms, name="terms"),
    path("email-collection-refusal/", views.email_refusal, name="email_refusal"),
    path("chapter/<slug:slug>/", views.chapter_detail, name="chapter"),
]
