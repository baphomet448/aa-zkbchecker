"""App URLs"""

# Django
from django.urls import path

# AA ZKB Checker App
from zkbchecker  import views

app_name: str = "zkbchecker"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.index, name="index"),
]
