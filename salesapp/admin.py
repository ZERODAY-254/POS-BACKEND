from django.contrib import admin
from django.utils.html import format_html

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
        'receipt_status',
        'receipt_actions',
        'created_at',
    )
    list_filter = ('payment_method', 'payment_status', 'created_at', 'is_active')
    search_fields = ('customer_name', 'receipt_number', 'invoice_number', 'payment_reference')
    readonly_fields = ('receipt_number', 'invoice_number', 'receipt_actions', 'created_at')

    @admin.display(description='Receipt')
    def receipt_status(self, obj):
        if obj.receipt_number:
            return 'Generated automatically'
        return 'Missing'

    @admin.display(description='Receipt / Invoice')
    def receipt_actions(self, obj):
        if not obj.pk:
            return 'Save the sale first'

        return format_html(
            '<a href="/api/sales/{}/receipt/" target="_blank">View receipt</a> | '
            '<a href="/api/sales/{}/print-receipt/" target="_blank">Print receipt</a> | '
            '<a href="/api/sales/{}/print-invoice/" target="_blank">Print invoice</a>',
            obj.pk,
            obj.pk,
            obj.pk,
        )
