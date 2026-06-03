from django.urls import path
from .views import home, help_page

urlpatterns = [
    path('', home, name='home'),
    path('help/', help_page, name='help'),
]
