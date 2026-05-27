from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_customuser_two_factor_enabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('storekeeper', 'StoreKeeper'),
                    ('cashier', 'Cashier'),
                    ('accountant', 'Accountant'),
                    ('customer', 'Customer'),
                    ('manager', 'Manager'),
                ],
                default='cashier',
                max_length=20,
            ),
        ),
    ]
