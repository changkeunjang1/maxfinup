from django.urls import path

from . import views

app_name = "ledger"

urlpatterns = [
    path("", views.home, name="home"),
    path("designs/", views.design_previews, name="designs"),
    path("trends/", views.trends, name="trends"),
    path("projects/trafficlens/", views.trafficlens, name="trafficlens"),
    path("projects/trafficlens/report/", views.trafficlens_report, name="trafficlens_report"),
    path("projects/trafficlens/slides/", views.trafficlens_slides, name="trafficlens_slides"),
    path("asset-management/", views.asset_management, name="asset_management"),
    path("asset-management/api/assets/", views.asset_api_list, name="asset_api_list"),
    path("asset-management/api/assets/<int:pk>/", views.asset_api_detail, name="asset_api_detail"),
    path("second-half/", views.second_half, name="second_half"),
    path("second-half/<slug:slug>/", views.second_half_topic, name="second_half_topic"),
    path("experts/", views.experts, name="experts"),
    path("experts/<slug:slug>/", views.asset_topic, name="asset_topic"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms, name="terms"),
    path("email-collection-refusal/", views.email_refusal, name="email_refusal"),
    path("chapter/<slug:slug>/", views.chapter_detail, name="chapter"),
]
