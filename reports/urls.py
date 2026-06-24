from django.urls import path

from . import document_views, views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('my/', views.my_progress, name='my_progress'),
    path('employees/', views.employee_report, name='employee_report'),
    path('departments/', views.department_report, name='department_report'),
    path('courses/', views.course_report, name='course_report'),
    path('employees/export/', views.export_employee_csv, name='employee_export_csv'),
    path('departments/export/', views.export_department_csv, name='department_export_csv'),
    path('courses/export/', views.export_course_csv, name='course_export_csv'),
    path(
        'documents/training-registry.xlsx',
        document_views.export_training_registry_xlsx,
        name='training_registry_xlsx',
    ),
    path(
        'documents/certificates/<int:assignment_id>.docx',
        document_views.download_assignment_certificate_docx,
        name='assignment_certificate_docx',
    ),
]
