"""Admin models"""

# Django
from django.contrib import admin

from zkbchecker.forms import ExcludedShipForm, SuspiciousEntityForm
from zkbchecker.models import ExcludedShip, SuspiciousEntity


@admin.register(SuspiciousEntity)
class SuspiciousEntityAdmin(admin.ModelAdmin):
    """Admin interface for suspicious alliances/corporations."""

    form = SuspiciousEntityForm
    list_display = ("label", "entity_type", "entity_id")
    list_filter = ("entity_type",)
    search_fields = ("label", "entity_id")
    ordering = ("label",)


@admin.register(ExcludedShip)
class ExcludedShipAdmin(admin.ModelAdmin):
    """Admin interface for excluded ship types."""

    form = ExcludedShipForm
    list_display = ("name", "ship_type_id")
    search_fields = ("name", "ship_type_id")
    ordering = ("name",)

    class Media:
        js = ("zkbchecker/js/excluded_ship_autocomplete.js",)