from django.urls import path
from .views import (
    product_list,
    product_detail,
    add_product,
    category_list,
    adjust_inventory,
    inventory_movements,
    conversion_preview,
    supplier_list,
    tax_code_list,
    unit_conversions,
    unit_list,
    update_product,
    delete_product,
    stock_alerts,
)

urlpatterns = [

    path('', product_list),
    path('<int:product_id>/', product_detail),
    path('categories/', category_list),
    path('suppliers/', supplier_list),
    path('units/', unit_list),
    path('unit-conversions/', unit_conversions),
    path('conversion-preview/', conversion_preview),
    path('tax-codes/', tax_code_list),
    path('stock-alerts/', stock_alerts),
    path('inventory/movements/', inventory_movements),
    path('inventory/adjust/', adjust_inventory),

    path('add/', add_product),

    path('update/<int:product_id>/', update_product),

    path('delete/<int:product_id>/', delete_product),
]
