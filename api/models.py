from django.db import models


class SavedReport(models.Model):
    REPORT_TYPES = (
        ('summary', 'Summary'),
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('payments', 'Payments'),
        ('profit', 'Profit'),
    )

    name = models.CharField(max_length=160)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    filters = models.JSONField(default=dict, blank=True)
    created_by = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ReportExport(models.Model):
    EXPORT_FORMATS = (
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    saved_report = models.ForeignKey(SavedReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='exports')
    report_type = models.CharField(max_length=30, choices=SavedReport.REPORT_TYPES)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_url = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    requested_by = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.report_type} export - {self.status}'


class Branch(models.Model):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return self.name


class Terminal(models.Model):
    STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('disabled', 'Disabled'),
    )

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='terminals')
    name = models.CharField(max_length=120)
    terminal_code = models.CharField(max_length=60, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Terminal'
        verbose_name_plural = 'Terminals'

    def __str__(self):
        return f'{self.branch.code} - {self.name}'


class ApprovalRequest(models.Model):
    ACTION_CHOICES = (
        ('return', 'Return'),
        ('refund', 'Refund'),
        ('discount', 'Discount'),
        ('void_sale', 'Void Sale'),
        ('stock_adjustment', 'Stock Adjustment'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('held', 'Held'),
    )

    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.CharField(max_length=120, blank=True)
    approved_by = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    reason = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    decision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Approval request'
        verbose_name_plural = 'Approval requests'

    def __str__(self):
        return f'{self.action_type} - {self.status}'


class OfflineSyncLog(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('conflict', 'Conflict'),
    )

    terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, blank=True, related_name='sync_logs')
    entity_type = models.CharField(max_length=80)
    local_id = models.CharField(max_length=120, blank=True)
    server_id = models.CharField(max_length=120, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Offline sync log'
        verbose_name_plural = 'Offline sync logs'

    def __str__(self):
        return f'{self.entity_type} - {self.status}'
