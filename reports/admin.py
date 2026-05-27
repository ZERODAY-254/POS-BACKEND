from django.contrib import admin

from .models import ReportExport, SavedReport


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'created_by', 'is_active', 'created_at')
    list_filter = ('report_type', 'is_active', 'created_at')
    search_fields = ('name', 'created_by')


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'export_format', 'status', 'requested_by', 'created_at', 'completed_at')
    list_filter = ('report_type', 'export_format', 'status', 'created_at')
    search_fields = ('requested_by', 'file_url', 'error_message')
