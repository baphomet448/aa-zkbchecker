"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Example App
from zkbchecker import __version__


class ExampleConfig(AppConfig):
    """App Config"""

    name = "zkbchecker"
    label = "zkbchecker"
    verbose_name = f"Example App v{__version__}"
