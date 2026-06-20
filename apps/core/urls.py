from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeLoginView.as_view(), name="home"),
    path("health/", views.health, name="health"),
]
