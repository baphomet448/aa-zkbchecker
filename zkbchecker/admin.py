"""Admin models"""

import re

from django import forms
from django.contrib import admin

from zkbchecker.models import ExcludedShip, SuspiciousEntity

ZKB_URL_PATTERN = re.compile(
    r"zkillboard\.com/(alliance|corporation)/(\d+)/?"
)


class SuspiciousEntityForm(forms.ModelForm):
    """Admin form that accepts a zKillboard URL and derives the
    entity type and ID from it, instead of requiring the admin to
    know the raw ID and type manually."""

    zkillboard_url = forms.CharField(
        label="zKillboard URL",
        help_text="Paste a zKillboard alliance or corporation URL, "
                   "e.g. https://zkillboard.com/alliance/99012042/ :)",
    )

    class Meta:
        model = SuspiciousEntity
        fields = ["zkillboard_url", "label"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            entity_type = self.instance.entity_type
            entity_id = self.instance.entity_id
            self.fields["zkillboard_url"].initial = (
                f"https://zkillboard.com/{entity_type}/{entity_id}/"
            )

    def clean_zkillboard_url(self):
        url = self.cleaned_data["zkillboard_url"]
        match = ZKB_URL_PATTERN.search(url)
        if not match:
            raise forms.ValidationError(
                "Could not find a valid zKillboard alliance/corporation URL "
                "in the provided text."
            )
        self.cleaned_data["entity_type"] = match.group(1)
        self.cleaned_data["entity_id"] = int(match.group(2))
        return url

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.entity_type = self.cleaned_data["entity_type"]
        instance.entity_id = self.cleaned_data["entity_id"]
        if commit:
            instance.save()
        return instance


@admin.register(SuspiciousEntity)
class SuspiciousEntityAdmin(admin.ModelAdmin):
    """Admin interface for suspicious alliances/corporations."""

    form = SuspiciousEntityForm
    list_display = ("label", "entity_type", "entity_id")
    list_filter = ("entity_type",)
    search_fields = ("label", "entity_id")
    ordering = ("label",)


class ExcludedShipForm(forms.ModelForm):
    """Admin form that hides the raw ship_type_id field; it's filled
    in automatically by JS when the admin picks a ship from the
    autocomplete suggestions."""

    class Meta:
        model = ExcludedShip
        fields = ["name", "ship_type_id"]
        widgets = {
            "ship_type_id": forms.HiddenInput(),
        }


@admin.register(ExcludedShip)
class ExcludedShipAdmin(admin.ModelAdmin):
    """Admin interface for excluded ship types."""

    form = ExcludedShipForm
    list_display = ("name", "ship_type_id")
    search_fields = ("name", "ship_type_id")
    ordering = ("name",)

    class Media:
        js = ("zkbchecker/js/excluded_ship_autocomplete.js",)