from django.urls import path

from .views import (
    approval_requests,
    branches,
    dashboard_charts,
    decide_approval,
    excel_export,
    excel_import_products,
    excel_template,
    inventory_report,
    offline_sync_logs,
    payments_report,
    react_payment_config,
    reports_summary,
    sales_report,
    terminal_heartbeat,
    terminals,
)


urlpatterns = [
    path('reports/summary/', reports_summary, name='reports_summary'),
    path('reports/sales/', sales_report, name='sales_report'),
    path('reports/inventory/', inventory_report, name='inventory_report'),
    path('reports/payments/', payments_report, name='payments_report'),
    path('dashboard/charts/', dashboard_charts, name='dashboard_charts'),
    path('react/payment-config/', react_payment_config, name='react_payment_config'),
    path('branches/', branches, name='branches'),
    path('terminals/', terminals, name='terminals'),
    path('terminals/heartbeat/', terminal_heartbeat, name='terminal_heartbeat'),
    path('approvals/', approval_requests, name='approval_requests'),
    path('approvals/<int:approval_id>/decide/', decide_approval, name='decide_approval'),
    path('offline-sync/', offline_sync_logs, name='offline_sync_logs'),
    path('excel/template/products/', excel_template, name='excel_template_products'),
    path('excel/export/<str:export_type>/', excel_export, name='excel_export'),
    path('excel/import/products/', excel_import_products, name='excel_import_products'),
]
