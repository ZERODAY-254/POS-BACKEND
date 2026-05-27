from django.urls import path

from api.views import (
    dashboard_charts,
    excel_export,
    excel_import_products,
    excel_template,
    inventory_report,
    payments_report,
    reports_summary,
    sales_report,
)


urlpatterns = [
    path('summary/', reports_summary, name='reports_app_summary'),
    path('sales/', sales_report, name='reports_app_sales'),
    path('inventory/', inventory_report, name='reports_app_inventory'),
    path('payments/', payments_report, name='reports_app_payments'),
    path('charts/', dashboard_charts, name='reports_app_charts'),
    path('excel/template/products/', excel_template, name='reports_app_excel_template_products'),
    path('excel/export/<str:export_type>/', excel_export, name='reports_app_excel_export'),
    path('excel/import/products/', excel_import_products, name='reports_app_excel_import_products'),
]
