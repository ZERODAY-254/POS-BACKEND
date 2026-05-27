from django.contrib import admin

from .models import CashDrawer, CashDrawerTransaction, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'amount', 'amount_received', 'method', 'status', 'reference', 'paid_at')
    list_filter = ('method', 'status', 'paid_at', 'is_active')
    search_fields = ('customer_name', 'reference', 'mpesa_receipt', 'terminal_reference')
    readonly_fields = ('paid_at',)


@admin.register(CashDrawer)
class CashDrawerAdmin(admin.ModelAdmin):
    list_display = ('name', 'cashier', 'status', 'opening_balance', 'expected_balance', 'closing_balance', 'opened_at')
    list_filter = ('status', 'opened_at', 'is_active')
    search_fields = ('name', 'cashier__username')
    readonly_fields = ('opened_at', 'closed_at')


@admin.register(CashDrawerTransaction)
class CashDrawerTransactionAdmin(admin.ModelAdmin):
    list_display = ('drawer', 'transaction_type', 'amount', 'payment', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('drawer__name', 'note')
    readonly_fields = ('created_at',)
