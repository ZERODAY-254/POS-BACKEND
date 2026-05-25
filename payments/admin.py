from django.contrib import admin

from .models import (
    CashDrawer,
    CashDrawerTransaction,
    MpesaTransaction,
    NotificationChannel,
    NotificationLog,
    NotificationRule,
    NotificationTemplate,
    Payment,
    PaymentNotification,
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'amount', 'amount_received', 'method', 'status', 'reference', 'paid_at')
    list_filter = ('method', 'status', 'paid_at', 'is_active')
    search_fields = ('customer_name', 'reference', 'mpesa_receipt', 'terminal_reference')
    readonly_fields = ('paid_at',)


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'amount', 'status', 'account_reference', 'checkout_request_id', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('phone_number', 'checkout_request_id', 'mpesa_receipt_number', 'account_reference')
    readonly_fields = ('created_at', 'updated_at', 'raw_request', 'raw_callback')


@admin.register(PaymentNotification)
class PaymentNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'severity', 'is_read', 'created_at')
    list_filter = ('channel', 'severity', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'read_at')
    actions = ('mark_selected_read',)

    @admin.action(description='Mark selected notifications as read')
    def mark_selected_read(self, request, queryset):
        queryset.update(is_read=True)


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_type', 'is_active', 'created_at')
    list_filter = ('channel_type', 'is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'subject', 'is_active', 'created_at')
    list_filter = ('channel', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'body')
    readonly_fields = ('created_at',)


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'template', 'is_active', 'created_at')
    list_filter = ('event', 'is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'channel', 'status', 'created_at', 'sent_at')
    list_filter = ('status', 'channel', 'created_at')
    search_fields = ('recipient', 'response')
    readonly_fields = ('created_at', 'sent_at')


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
