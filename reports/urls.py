from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.my_progress, name='my_progress'),
    path('analytics/', views.analytics, name='analytics'),
    path('export/', views.export_csv, name='export_csv'),
]
