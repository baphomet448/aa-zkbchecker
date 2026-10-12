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
    path("ship-list/", views.ship_list, name="ship_list"),
    path("settings/", views.config_settings, name="settings"),
    path("settings/entity/<int:pk>/delete/", views.delete_suspicious_entity, name="delete_entity"),
    path("settings/ship/<int:pk>/delete/", views.delete_excluded_ship, name="delete_ship"),
]