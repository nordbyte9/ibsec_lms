from django.contrib import admin

from .models import IntegrationSyncLog


@admin.register(IntegrationSyncLog)
class IntegrationSyncLogAdmin(admin.ModelAdmin):
    list_display = (
        'started_at',
        'finished_at',
        'source',
        'status',
        'imported_departments',
        'imported_positions',
        'imported_users',
    )
    list_filter = ('source', 'status', 'started_at')
    search_fields = ('message',)
