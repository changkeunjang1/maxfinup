from django.urls import path

from . import views

app_name = "ledger"

urlpatterns = [
    path("", views.home, name="home"),
    path("designs/", views.design_previews, name="designs"),
    path("chapter/<slug:slug>/", views.chapter_detail, name="chapter"),
]
