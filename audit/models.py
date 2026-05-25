from django.db import models


class AuditLog(models.Model):
    actor = models.CharField(max_length=100, blank=True)
    action = models.CharField(max_length=120)
    module = models.CharField(max_length=80)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.module} - {self.action}'
