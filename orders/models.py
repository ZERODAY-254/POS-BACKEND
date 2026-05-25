from django.db import models


class Order(models.Model):

    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bank', 'Bank Transfer'),
        ('mixed', 'Multiple Methods'),
    )

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    ORDER_STATUS = (
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    customer_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    delivery_address = models.CharField(max_length=255)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS, default='mpesa')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='placed')
    tracking_code = models.CharField(max_length=30, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.unit_price * self.quantity

        super().save(*args, **kwargs)

        if not self.tracking_code:
            self.tracking_code = f'ORD-{self.id:06d}'
            super().save(update_fields=['tracking_code'])

    def __str__(self):
        return self.tracking_code or self.customer_name
