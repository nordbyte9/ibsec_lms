from django.urls import path

from . import views

app_name = 'assignments'

urlpatterns = [
    path('my/', views.my_assignments, name='my'),
    path('', views.assignment_list, name='list'),
    path('create/', views.assignment_create, name='create'),
]
