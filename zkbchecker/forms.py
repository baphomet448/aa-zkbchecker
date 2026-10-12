"""Forms shared by the Django admin and the plugin's own settings page."""

import re

from django import forms
from django.utils.translation import gettext_lazy as _

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
        label=_("zKillboard URL"),
        help_text=_(
            "Paste a zKillboard alliance or corporation URL, "
            "e.g. https://zkillboard.com/alliance/99012042/"
        ),
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
        self.fields["zkillboard_url"].error_messages["required"] = _(
            "Please paste a zKillboard URL."
        )
        self.fields["label"].label = _("Label")
        self.fields["label"].help_text = _(
            "Displayed in results when this entity is matched."
        )
        self.fields["label"].widget.attrs["placeholder"] = _("Label")
        self.fields["label"].error_messages["required"] = _("Please enter a label.")
        self._apply_bootstrap()

    def clean_zkillboard_url(self):
        url = self.cleaned_data["zkillboard_url"]
        match = ZKB_URL_PATTERN.search(url)
        if not match:
            raise forms.ValidationError(
                _(
                    "Could not find a valid zKillboard alliance/corporation URL "
                    "in the provided text."
                )
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
                    _("This alliance/corporation is already in the list.")
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
        name = self.fields["name"]
        name.label = _("Name")
        name.help_text = _("Start typing to search for a ship.")
        name.widget.attrs["placeholder"] = _("Start typing a ship or item name...")
        name.error_messages["required"] = _("Please enter an item name.")
        # Texts for the autocomplete JS, which is a static file and can't
        # use Django's translation tags itself.
        name.widget.attrs["data-selected-label"] = _("Selected ship type ID")
        name.widget.attrs["data-none-label"] = _("No ship selected yet.")
        self.fields["ship_type_id"].error_messages["required"] = _(
            "Please choose an item from the suggestion list."
        )
        self._apply_bootstrap()