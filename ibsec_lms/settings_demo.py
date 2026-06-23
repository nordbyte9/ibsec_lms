"""Settings used only by the isolated demonstration environment."""

from .settings import *  # noqa: F401,F403

INSTALLED_APPS = [*INSTALLED_APPS, 'demo.apps.DemoConfig']  # noqa: F405
