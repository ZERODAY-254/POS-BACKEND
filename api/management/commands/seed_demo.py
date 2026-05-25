from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from customers.models import Customer
from orders.models import Order
from payments.models import Payment
from products.models import Product
from returns.models import Return
from salesapp.models import Sale


class Command(BaseCommand):
    help = "Seed demo data for local development."

    def handle(self, *args, **options):
        User = get_user_model()

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin12345")
            admin.save()

        products = [
            {
                "name": "Premium Sugar 2kg",
                "description": "Fast-moving household staple.",
                "price": Decimal("220.00"),
                "quantity": 48,
            },
            {
                "name": "Fresh Milk 500ml",
                "description": "Daily dairy product for retail checkout.",
                "price": Decimal("75.00"),
                "quantity": 80,
            },
            {
                "name": "Cooking Oil 3L",
                "description": "High-value grocery inventory item.",
                "price": Decimal("780.00"),
                "quantity": 25,
            },
        ]

        for item in products:
            Product.objects.get_or_create(name=item["name"], defaults=item)

        customers = [
            {
                "name": "Amina Otieno",
                "email": "amina@example.com",
                "phone": "0712345678",
                "address": "Nairobi CBD",
            },
            {
                "name": "Brian Mwangi",
                "email": "brian@example.com",
                "phone": "0798765432",
                "address": "Westlands",
            },
        ]

        for customer in customers:
            Customer.objects.get_or_create(email=customer["email"], defaults=customer)

        Sale.objects.get_or_create(
            customer_name="Amina Otieno",
            amount=Decimal("1540.00"),
        )
        Payment.objects.get_or_create(
            customer_name="Amina Otieno",
            amount=Decimal("1540.00"),
            method="mpesa",
            status="paid",
            mpesa_phone="254712345678",
            mpesa_receipt="QK12DEMO",
        )
        Order.objects.get_or_create(
            customer_name="Brian Mwangi",
            phone="0798765432",
            delivery_address="Westlands, Nairobi",
            product_name="Cooking Oil 3L",
            quantity=2,
            unit_price=Decimal("780.00"),
            total_amount=Decimal("1560.00"),
            payment_method="mpesa",
            payment_status="paid",
            status="confirmed",
        )
        Return.objects.get_or_create(
            customer_name="Amina Otieno",
            item_name="Fresh Milk 500ml",
            amount=Decimal("75.00"),
            reason="Damaged packaging",
            status="approved",
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready. Admin login: admin / admin12345"))
