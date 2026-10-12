"""Forms shared by the Django admin and the plugin's own settings page."""

import re

from django import forms

from zkbchecker.models import ExcludedShip, SuspiciousEntity

ZKB_URL_PATTERN = re.compile(
    r"zkillboard\.com/(alliance|corporation)/(\d+)/?"
)


class BootstrapFieldsMixin:
    """Adds Bootstrap's form-control class to visible widgets so the
    forms look right on the plugin's own pages (harmless in the Django
    admin, which doesn't style that class)."""

    def _apply_bootstrap(self):
        for field in self.fields.values():
            if not field.widget.is_hidden:
                field.widget.attrs.setdefault("class", "form-control")


class SuspiciousEntityForm(BootstrapFieldsMixin, forms.ModelForm):
    """Form that accepts a zKillboard URL and derives the entity type
    and ID from it, instead of requiring the user to know the raw ID
    and type manually."""

    zkillboard_url = forms.CharField(
        label="zKillboard URL",
        help_text="Paste a zKillboard alliance or corporation URL, "
                  "e.g. https://zkillboard.com/alliance/99012042/",
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
        self.fields["zkillboard_url"].widget.attrs["placeholder"] = (
            "https://zkillboard.com/alliance/99012042/"
        )
        self.fields["label"].widget.attrs["placeholder"] = "Label"
        self.fields["zkillboard_url"].error_messages["required"] = (
            "Please paste a zKillboard URL."
        )
        self.fields["label"].error_messages["required"] = "Please enter a label."
        self._apply_bootstrap()

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

    def clean(self):
        cleaned = super().clean()
        entity_type = cleaned.get("entity_type")
        entity_id = cleaned.get("entity_id")
        if entity_type and entity_id:
            duplicates = SuspiciousEntity.objects.filter(
                entity_type=entity_type, entity_id=entity_id
            )
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    "This alliance/corporation is already in the list."
                )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.entity_type = self.cleaned_data["entity_type"]
        instance.entity_id = self.cleaned_data["entity_id"]
        if commit:
            instance.save()
        return instance


class ExcludedShipForm(BootstrapFieldsMixin, forms.ModelForm):
    """Form that hides the raw ship_type_id field; it's filled in
    automatically by JS when the user picks a ship from the
    autocomplete suggestions."""

    class Meta:
        model = ExcludedShip
        fields = ["name", "ship_type_id"]
        widgets = {
            "ship_type_id": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["placeholder"] = (
            "Start typing a ship or item name..."
        )
        self.fields["name"].error_messages["required"] = "Please enter an item name."
        self.fields["ship_type_id"].error_messages["required"] = (
            "Please choose an item from the suggestion list."
        )
        self._apply_bootstrap()