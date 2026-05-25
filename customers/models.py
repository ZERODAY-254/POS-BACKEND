from django.db import models


class Customer(models.Model):

    name = models.CharField(max_length=100)
    account_reference = models.CharField(max_length=50, blank=True)

    email = models.EmailField()

    phone = models.CharField(max_length=20)

    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
