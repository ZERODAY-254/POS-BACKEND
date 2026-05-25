from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('storekeeper', 'StoreKeeper'),
        ('cashier', 'Cashier'),
        ('customer', 'Customer'),
        ('manager', 'Manager')
    )

    ACCESS_TIER_CHOICES = (
        ('standard', 'Standard'),
        ('supervisor', 'Supervisor'),
        ('administrator', 'Administrator'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='cashier'
    )

    access_tier = models.CharField(
        max_length=20,
        choices=ACCESS_TIER_CHOICES,
        default='standard'
    )

    two_factor_enabled = models.BooleanField(default=True)
    two_factor_code = models.CharField(max_length=6, blank=True)
    two_factor_verified_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username
