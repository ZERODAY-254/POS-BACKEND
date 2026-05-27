from django.contrib import admin

from .models import MpesaTransaction


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'amount', 'status', 'account_reference', 'checkout_request_id', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('phone_number', 'checkout_request_id', 'mpesa_receipt_number', 'account_reference')
    readonly_fields = ('created_at', 'updated_at', 'raw_request', 'raw_callback')
