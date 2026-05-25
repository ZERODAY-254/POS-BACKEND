from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('module', 'action', 'actor', 'created_at')
    search_fields = ('module', 'action', 'actor', 'details')
    readonly_fields = ('created_at',)
