from decimal import Decimal
from django.db import models

class Sale(models.Model):

    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
        ('mixed', 'Mixed Payment'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    )

    customer_name = models.CharField(max_length=100)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='paid')
    payment_reference = models.CharField(max_length=100, blank=True)
    mpesa_phone = models.CharField(max_length=20, blank=True)
    receipt_number = models.CharField(max_length=30, blank=True)
    invoice_number = models.CharField(max_length=30, blank=True)
    items = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.subtotal:
            self.subtotal = self.amount

        if not self.grand_total:
            self.grand_total = self.subtotal - self.discount + self.tax

        self.amount = self.grand_total
        self.profit = Decimal(self.grand_total or 0) - Decimal(self.cost_total or 0)
        self.change_due = max(
            Decimal(self.amount_paid or 0) - Decimal(self.grand_total or 0),
            Decimal('0')
        )

        super().save(*args, **kwargs)

        if not self.receipt_number:
            self.receipt_number = f'RCPT-{self.id:06d}'
            self.invoice_number = self.invoice_number or f'INV-{self.id:06d}'
            super().save(update_fields=['receipt_number', 'invoice_number'])

    def __str__(self):
        return self.customer_name
