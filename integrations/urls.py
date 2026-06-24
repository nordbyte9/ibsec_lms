from django.urls import path

from . import views

app_name = 'integrations'

urlpatterns = [
    path('', views.integration_index, name='index'),
    path('example/', views.download_sample, name='sample'),
]
