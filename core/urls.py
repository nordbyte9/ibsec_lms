from django.urls import path

from .health import health_check
from .views import help_page, home

urlpatterns = [
    path('', home, name='home'),
    path('help/', help_page, name='help'),
    path('health/', health_check, name='health'),
]
