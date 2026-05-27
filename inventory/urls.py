from django.urls import path

from products.views import (
    adjust_inventory,
    conversion_preview,
    inventory_movements,
    stock_alerts,
    supplier_list,
    unit_conversions,
    unit_list,
)


urlpatterns = [
    path('movements/', inventory_movements, name='inventory_app_movements'),
    path('adjust/', adjust_inventory, name='inventory_app_adjust'),
    path('stock-alerts/', stock_alerts, name='inventory_app_stock_alerts'),
    path('suppliers/', supplier_list, name='inventory_app_suppliers'),
    path('units/', unit_list, name='inventory_app_units'),
    path('unit-conversions/', unit_conversions, name='inventory_app_unit_conversions'),
    path('conversion-preview/', conversion_preview, name='inventory_app_conversion_preview'),
]
