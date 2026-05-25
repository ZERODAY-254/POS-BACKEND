from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'tracking_code',
        'customer_name',
        'product_name',
        'total_amount',
        'payment_method',
        'payment_status',
        'status',
        'created_at',
    )
    search_fields = ('tracking_code', 'customer_name', 'product_name', 'phone')
    list_filter = ('payment_method', 'payment_status', 'status')
