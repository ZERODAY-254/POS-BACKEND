from products.models import (
    Batch as BaseBatch,
    InventoryMovement as BaseInventoryMovement,
    ProductUnit as BaseProductUnit,
    ProductUnitConversion as BaseProductUnitConversion,
    Supplier as BaseSupplier,
)


class Supplier(BaseSupplier):
    class Meta:
        proxy = True
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'


class ProductUnit(BaseProductUnit):
    class Meta:
        proxy = True
        verbose_name = 'Product unit'
        verbose_name_plural = 'Product units'


class ProductUnitConversion(BaseProductUnitConversion):
    class Meta:
        proxy = True
        verbose_name = 'Product unit conversion'
        verbose_name_plural = 'Product unit conversions'


class Batch(BaseBatch):
    class Meta:
        proxy = True
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'


class InventoryMovement(BaseInventoryMovement):
    class Meta:
        proxy = True
        verbose_name = 'Inventory movement'
        verbose_name_plural = 'Inventory movements'
