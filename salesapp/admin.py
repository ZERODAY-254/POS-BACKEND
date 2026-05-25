from django.contrib import admin

from .models import Sale


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number',
        'invoice_number',
        'customer_name',
        'grand_total',
        'profit',
        'payment_method',
        'payment_status',
        'created_at',
    )
    list_filter = ('payment_method', 'payment_status', 'created_at', 'is_active')
    search_fields = ('customer_name', 'receipt_number', 'invoice_number', 'payment_reference')
    readonly_fields = ('receipt_number', 'invoice_number', 'created_at')
