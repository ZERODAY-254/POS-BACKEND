from django.contrib import admin

from .models import ApprovalRequest, Branch, OfflineSyncLog, ReportExport, SavedReport, Terminal


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'created_by', 'is_active', 'created_at')
    list_filter = ('report_type', 'is_active', 'created_at')
    search_fields = ('name', 'created_by')
    readonly_fields = ('created_at',)


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'export_format', 'status', 'requested_by', 'created_at', 'completed_at')
    list_filter = ('report_type', 'export_format', 'status', 'created_at')
    search_fields = ('requested_by', 'file_url', 'error_message')
    readonly_fields = ('created_at', 'completed_at')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'phone', 'email')


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'terminal_code', 'branch', 'status', 'ip_address', 'last_seen_at', 'is_active')
    list_filter = ('branch', 'status', 'is_active')
    search_fields = ('name', 'terminal_code', 'ip_address')


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'status', 'reference', 'requested_by', 'approved_by', 'created_at', 'decided_at')
    list_filter = ('action_type', 'status', 'created_at')
    search_fields = ('reference', 'requested_by', 'approved_by', 'reason')
    readonly_fields = ('created_at', 'decided_at')


@admin.register(OfflineSyncLog)
class OfflineSyncLogAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'local_id', 'server_id', 'terminal', 'status', 'created_at', 'synced_at')
    list_filter = ('entity_type', 'status', 'terminal', 'created_at')
    search_fields = ('entity_type', 'local_id', 'server_id', 'error_message')
