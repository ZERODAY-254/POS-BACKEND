from django.contrib import admin

from .models import (
    Batch,
    Category,
    InventoryMovement,
    Product,
    ProductImage,
    ProductUnit,
    ProductUnitConversion,
    Supplier,
    TaxCode,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_person', 'phone', 'email')


@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'is_base_unit', 'is_active', 'created_at')
    list_filter = ('is_base_unit', 'is_active', 'created_at')
    search_fields = ('name', 'symbol')


@admin.register(TaxCode)
class TaxCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rate', 'tax_type', 'is_exempt', 'is_active')
    list_filter = ('tax_type', 'is_exempt', 'is_active')
    search_fields = ('code', 'name', 'kra_pin')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'supplier',
        'base_unit',
        'tax_code',
        'sku',
        'barcode',
        'cost_price',
        'price',
        'wholesale_price',
        'quantity',
        'minimum_stock',
        'is_active',
        'created_at',
    )
    list_filter = ('category', 'supplier', 'base_unit', 'tax_code', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'sku', 'barcode')
    readonly_fields = ('created_at',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('created_at',)


@admin.register(ProductUnitConversion)
class ProductUnitConversionAdmin(admin.ModelAdmin):
    list_display = ('product', 'unit', 'base_quantity', 'retail_price', 'wholesale_price', 'barcode', 'is_active')
    list_filter = ('unit', 'is_active')
    search_fields = ('product__name', 'product__sku', 'barcode')


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'product', 'supplier', 'quantity', 'cost_price', 'expiry_date', 'received_at', 'is_active')
    list_filter = ('supplier', 'expiry_date', 'received_at', 'is_active')
    search_fields = ('batch_number', 'product__name', 'supplier__name')
    readonly_fields = ('received_at',)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'movement_type',
        'quantity',
        'previous_quantity',
        'new_quantity',
        'reference',
        'actor',
        'created_at',
    )
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'reference', 'note', 'actor')
    readonly_fields = ('created_at',)
