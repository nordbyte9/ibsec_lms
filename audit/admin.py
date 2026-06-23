from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'object_type', 'object_id', 'ip_address')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('user__username', 'action', 'description')
