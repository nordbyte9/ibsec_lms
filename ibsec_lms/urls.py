from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("knowledge/", include("knowledge.urls")),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('assignments/', include('assignments.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('reports/', include('reports.urls')),
    path('audit/', include('audit.urls')),
    path('integrations/', include('integrations.urls')),
]
