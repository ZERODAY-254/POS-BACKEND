from django.db import models
from products.models import Product


class Sale(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    sold_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        self.total_price = (
            self.product.price * self.quantity
        )

        self.product.quantity -= self.quantity
        self.product.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.product.name