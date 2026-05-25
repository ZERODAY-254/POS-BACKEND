from django.db import models
from django.conf import settings


class Payment(models.Model):

    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
    )

    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    )

    customer_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    reference = models.CharField(max_length=100, blank=True)
    mpesa_phone = models.CharField(max_length=20, blank=True)
    mpesa_receipt = models.CharField(max_length=100, blank=True)
    card_last_four = models.CharField(max_length=4, blank=True)
    terminal_reference = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.method == 'cash':
            self.change_due = max(self.amount_received - self.amount, 0)
        else:
            self.amount_received = self.amount
            self.change_due = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.customer_name} - {self.amount}'


class MpesaTransaction(models.Model):

    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_transactions')
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=100, blank=True)
    merchant_request_id = models.CharField(max_length=120, blank=True)
    checkout_request_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    result_code = models.CharField(max_length=20, blank=True)
    result_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    raw_request = models.JSONField(default=dict, blank=True)
    raw_callback = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.phone_number} - {self.amount} - {self.status}'


class PaymentNotification(models.Model):

    CHANNEL_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('system', 'System'),
        ('drawer', 'Cash Drawer'),
        ('inventory', 'Inventory'),
        ('reports', 'Reports'),
        ('sales', 'Sales'),
    )

    SEVERITY_CHOICES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='system')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    title = models.CharField(max_length=160)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    mpesa_transaction = models.ForeignKey(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class NotificationChannel(models.Model):
    CHANNEL_TYPES = (
        ('system', 'System'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('mpesa', 'M-Pesa'),
        ('inventory', 'Inventory'),
    )

    name = models.CharField(max_length=120)
    channel_type = models.CharField(max_length=30, choices=CHANNEL_TYPES, default='system')
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class NotificationTemplate(models.Model):
    name = models.CharField(max_length=120)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.SET_NULL, null=True, blank=True, related_name='templates')
    subject = models.CharField(max_length=160, blank=True)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class NotificationRule(models.Model):
    EVENT_CHOICES = (
        ('low_stock', 'Low Stock'),
        ('sale_created', 'Sale Created'),
        ('mpesa_success', 'M-Pesa Success'),
        ('mpesa_failed', 'M-Pesa Failed'),
        ('daily_report', 'Daily Report'),
    )

    name = models.CharField(max_length=120)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='rules')
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class NotificationLog(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    notification = models.ForeignKey(PaymentNotification, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    recipient = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.recipient or "notification"} - {self.status}'


class CashDrawer(models.Model):

    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
    )

    name = models.CharField(max_length=100)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expected_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} - {self.status}'


class CashDrawerTransaction(models.Model):

    TRANSACTION_TYPES = (
        ('sale', 'Sale'),
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('refund', 'Refund'),
        ('opening', 'Opening Balance'),
        ('closing', 'Closing Balance'),
    )

    drawer = models.ForeignKey(CashDrawer, on_delete=models.CASCADE, related_name='transactions')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.drawer.name} - {self.transaction_type} - {self.amount}'
