from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=160)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductUnit(models.Model):
    name = models.CharField(max_length=80, unique=True)
    symbol = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_base_unit = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.symbol or self.name


class TaxCode(models.Model):
    TAX_TYPES = (
        ('sales', 'Sales Tax'),
        ('purchase', 'Purchase Tax'),
        ('both', 'Sales and Purchase Tax'),
    )

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES, default='sales')
    is_exempt = models.BooleanField(default=False)
    kra_pin = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tax code'
        verbose_name_plural = 'Tax codes'

    def __str__(self):
        return f'{self.code} - {self.rate}%'


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    base_unit = models.ForeignKey(ProductUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='base_products')
    tax_code = models.ForeignKey(TaxCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    sku = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    image_data = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock

    def __str__(self):
        return self.name

    def unit_ratio(self, unit_id=None):
        if not unit_id:
            return 1

        conversion = self.unit_conversions.filter(unit_id=unit_id, is_active=True).first()
        return conversion.base_quantity if conversion else 1

    def selling_price_for(self, unit_id=None, price_type='retail'):
        base_price = self.wholesale_price if price_type == 'wholesale' and self.wholesale_price else self.price
        return base_price * self.unit_ratio(unit_id)

    def tax_amount_for(self, taxable_amount):
        if not self.tax_code or self.tax_code.is_exempt:
            return 0
        return taxable_amount * (self.tax_code.rate / 100)


class ProductUnitConversion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='unit_conversions')
    unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, related_name='product_conversions')
    base_quantity = models.PositiveIntegerField(default=1)
    barcode = models.CharField(max_length=50, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'unit')
        verbose_name = 'Product unit conversion'
        verbose_name_plural = 'Product unit conversions'

    def __str__(self):
        return f'{self.product.name}: 1 {self.unit} = {self.base_quantity} base units'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(blank=True)
    image_data = models.TextField(blank=True)
    alt_text = models.CharField(max_length=160, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product image'
        verbose_name_plural = 'Product images'

    def __str__(self):
        return f'{self.product.name} image'


class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    batch_number = models.CharField(max_length=80)
    quantity = models.IntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'batch_number')
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'

    def __str__(self):
        return f'{self.product.name} - {self.batch_number}'


class InventoryMovement(models.Model):
    MOVEMENT_TYPES = (
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('damage', 'Damage'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField(default=0)
    new_quantity = models.IntegerField(default=0)
    reference = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    actor = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inventory movement'
        verbose_name_plural = 'Inventory movements'

    def __str__(self):
        return f'{self.product.name} - {self.movement_type} - {self.quantity}'
