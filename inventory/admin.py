from django.contrib import admin

from .models import Batch, InventoryMovement, ProductUnit, ProductUnitConversion, Supplier


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


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'previous_quantity', 'new_quantity', 'reference', 'actor', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'reference', 'note', 'actor')
