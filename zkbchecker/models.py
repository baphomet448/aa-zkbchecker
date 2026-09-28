"""
App Models
Create your models in here
"""

# Django
from django.db import models


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        """Meta definitions"""

        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("manage_config", "Can manage suspicious alliances/corps and excluded ships"),
        )


class ExcludedShip(models.Model):
    """A ship type to exclude from loss statistics (capsules,
    mobile structures, etc.)."""

    name = models.CharField(max_length=255, help_text="For readability only, not used in logic.")
    ship_type_id = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.ship_type_id})"


class SuspiciousEntity(models.Model):
    """An alliance or corporation considered suspicious when seen as
    the final-blow attacker on a checked character's kills."""

    class EntityType(models.TextChoices):
        ALLIANCE = "alliance", "Alliance"
        CORPORATION = "corporation", "Corporation"

    entity_id = models.PositiveIntegerField()
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    label = models.CharField(max_length=255, help_text="Displayed in results when this entity is matched.")

    class Meta:
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(
                fields=["entity_id", "entity_type"],
                name="unique_entity_id_per_type",
            )
        ]

    def __str__(self) -> str:
        return f"{self.label} ({self.get_entity_type_display()}, {self.entity_id})"