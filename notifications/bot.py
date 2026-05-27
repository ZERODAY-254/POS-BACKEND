from django.db.models import Count, Sum
from django.utils import timezone

from payments.models import MpesaTransaction, PaymentNotification
from products.models import Product
from salesapp.models import Sale


class NotificationBot:
    name = 'POS Notification Bot'

    def notify(self, channel, severity, title, message, action_url=''):
        notification, created = PaymentNotification.objects.get_or_create(
            channel=channel,
            severity=severity,
            title=title,
            message=message,
            is_read=False,
            defaults={'action_url': action_url},
        )
        return notification, created

    def scan_low_stock(self):
        created_count = 0
        products = Product.objects.filter(is_active=True, quantity__lte=models.F('minimum_stock'))
        for product in products:
            _, created = self.notify(
                channel='inventory',
                severity='warning',
                title='Low stock alert',
                message=f'{product.name} stock is {product.quantity}. Minimum is {product.minimum_stock}.',
                action_url='/inventory',
            )
            created_count += int(created)
        return created_count

    def scan_pending_mpesa(self):
        created_count = 0
        cutoff = timezone.now() - timezone.timedelta(minutes=10)
        transactions = MpesaTransaction.objects.filter(status='pending', created_at__lte=cutoff)
        for transaction in transactions:
            _, created = self.notify(
                channel='mpesa',
                severity='warning',
                title='Pending M-Pesa transaction',
                message=f'M-Pesa transaction {transaction.checkout_request_id or transaction.id} is still pending.',
                action_url='/payments',
            )
            created_count += int(created)
        return created_count

    def scan_failed_mpesa(self):
        created_count = 0
        transactions = MpesaTransaction.objects.filter(status='failed', updated_at__date=timezone.localdate())
        for transaction in transactions:
            _, created = self.notify(
                channel='mpesa',
                severity='error',
                title='Failed M-Pesa transaction',
                message=transaction.result_description or f'M-Pesa transaction {transaction.id} failed.',
                action_url='/payments',
            )
            created_count += int(created)
        return created_count

    def daily_summary(self):
        today = timezone.localdate()
        totals = Sale.objects.filter(is_active=True, created_at__date=today).aggregate(
            total=Sum('grand_total'),
            count=Count('id'),
        )
        _, created = self.notify(
            channel='reports',
            severity='info',
            title='Daily sales summary',
            message=f"Today sales: KES {totals['total'] or 0}. Transactions: {totals['count'] or 0}.",
            action_url='/reports',
        )
        return int(created)

    def run(self):
        return {
            'low_stock': self.scan_low_stock(),
            'pending_mpesa': self.scan_pending_mpesa(),
            'failed_mpesa': self.scan_failed_mpesa(),
            'daily_summary': self.daily_summary(),
        }


# Avoid importing django.db.models as "models" at module top before Django app loading in some contexts.
from django.db import models  # noqa: E402
