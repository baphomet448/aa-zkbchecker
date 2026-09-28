"""App URLs"""

# Django
from django.urls import path

# AA ZKB Checker App
from zkbchecker import views

app_name: str = "zkbchecker"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.index, name="index"),
    path("start-check/", views.start_check, name="start_check"),
    path("check-status/<str:task_id>/", views.check_status, name="check_status"),
    path("export-excel/", views.export_excel, name="export_excel"),
]