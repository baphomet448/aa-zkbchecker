"""App Configuration"""

# Django
from django.apps import AppConfig

# AA ZKB Checker App
from zkbchecker import __version__


class ZkbCheckerConfig(AppConfig):
    """App Config"""

    name = "zkbchecker"
    label = "zkbchecker"
    verbose_name = f"ZKB Checker v{__version__}"