from django.contrib import admin

from .models import Category, Product, ProductImage, TaxCode


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')


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
