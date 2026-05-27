from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from customers.models import Customer
from payments.models import MpesaTransaction, Payment
from products.models import InventoryMovement, Product, Supplier
from salesapp.models import Sale

from .excel import build_xlsx


EXPORT_DIR = Path(getattr(settings, 'EXCEL_EXPORT_DIR', settings.BASE_DIR / 'exports'))
AUTO_SYNC_ENABLED = getattr(settings, 'EXCEL_AUTO_SYNC_ENABLED', True)


def write_workbook(filename, sheet_name, headers, rows):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_bytes(build_xlsx(sheet_name, headers, rows))
    return path


def product_rows():
    products = Product.objects.select_related('category', 'supplier', 'base_unit', 'tax_code').order_by('id')
    return [
        [
            product.id,
            product.name,
            product.sku,
            product.barcode,
            product.category.name if product.category else '',
            product.supplier.name if product.supplier else '',
            product.base_unit.name if product.base_unit else '',
            product.tax_code.code if product.tax_code else '',
            product.cost_price,
            product.price,
            product.wholesale_price,
            product.quantity,
            product.minimum_stock,
            'yes' if product.is_low_stock else 'no',
            product.is_active,
            product.created_at,
        ]
        for product in products
    ]


def sale_rows():
    sales = Sale.objects.order_by('id')
    return [
        [
            sale.id,
            sale.receipt_number,
            sale.invoice_number,
            sale.customer_name,
            sale.subtotal,
            sale.discount,
            sale.tax,
            sale.grand_total,
            sale.amount_paid,
            sale.change_due,
            sale.payment_method,
            sale.payment_status,
            sale.payment_reference,
            sale.profit,
            len(sale.items or []),
            sale.is_active,
            sale.created_at,
        ]
        for sale in sales
    ]


def customer_rows():
    customers = Customer.objects.order_by('id')
    return [
        [
            customer.id,
            customer.name,
            customer.account_reference,
            customer.email,
            customer.phone,
            customer.address,
            customer.is_active,
        ]
        for customer in customers
    ]


def supplier_rows():
    suppliers = Supplier.objects.order_by('id')
    return [
        [
            supplier.id,
            supplier.name,
            supplier.contact_person,
            supplier.email,
            supplier.phone,
            supplier.address,
            supplier.is_active,
            supplier.created_at,
        ]
        for supplier in suppliers
    ]


def payment_rows():
    payments = Payment.objects.order_by('id')
    return [
        [
            payment.id,
            payment.customer_name,
            payment.amount,
            payment.amount_received,
            payment.change_due,
            payment.method,
            payment.status,
            payment.reference,
            payment.mpesa_phone,
            payment.mpesa_receipt,
            payment.is_active,
            payment.paid_at,
        ]
        for payment in payments
    ]


def mpesa_rows():
    transactions = MpesaTransaction.objects.select_related('payment').order_by('id')
    return [
        [
            item.id,
            item.payment_id or '',
            item.phone_number,
            item.amount,
            item.account_reference,
            item.merchant_request_id,
            item.checkout_request_id,
            item.mpesa_receipt_number,
            item.result_code,
            item.result_description,
            item.status,
            item.created_at,
            item.updated_at,
        ]
        for item in transactions
    ]


def movement_rows():
    movements = InventoryMovement.objects.select_related('product').order_by('id')
    return [
        [
            movement.id,
            movement.product.name,
            movement.movement_type,
            movement.quantity,
            movement.previous_quantity,
            movement.new_quantity,
            movement.reference,
            movement.actor,
            movement.note,
            movement.created_at,
        ]
        for movement in movements
    ]


EXPORTS = {
    'products': {
        'filename': 'products.xlsx',
        'sheet': 'Products',
        'headers': [
            'id', 'name', 'sku', 'barcode', 'category', 'supplier', 'base_unit', 'tax_code',
            'cost_price', 'retail_price', 'wholesale_price', 'quantity', 'minimum_stock',
            'low_stock', 'is_active', 'created_at',
        ],
        'rows': product_rows,
    },
    'sales': {
        'filename': 'sales.xlsx',
        'sheet': 'Sales',
        'headers': [
            'id', 'receipt_number', 'invoice_number', 'customer_name', 'subtotal', 'discount',
            'tax', 'grand_total', 'amount_paid', 'change_due', 'payment_method',
            'payment_status', 'payment_reference', 'profit', 'item_count', 'is_active', 'created_at',
        ],
        'rows': sale_rows,
    },
    'customers': {
        'filename': 'customers.xlsx',
        'sheet': 'Customers',
        'headers': ['id', 'name', 'account_reference', 'email', 'phone', 'address', 'is_active'],
        'rows': customer_rows,
    },
    'suppliers': {
        'filename': 'suppliers.xlsx',
        'sheet': 'Suppliers',
        'headers': ['id', 'name', 'contact_person', 'email', 'phone', 'address', 'is_active', 'created_at'],
        'rows': supplier_rows,
    },
    'payments': {
        'filename': 'payments.xlsx',
        'sheet': 'Payments',
        'headers': [
            'id', 'customer_name', 'amount', 'amount_received', 'change_due', 'method', 'status',
            'reference', 'mpesa_phone', 'mpesa_receipt', 'is_active', 'paid_at',
        ],
        'rows': payment_rows,
    },
    'mpesa': {
        'filename': 'mpesa_transactions.xlsx',
        'sheet': 'M-Pesa',
        'headers': [
            'id', 'payment_id', 'phone_number', 'amount', 'account_reference', 'merchant_request_id',
            'checkout_request_id', 'mpesa_receipt_number', 'result_code', 'result_description',
            'status', 'created_at', 'updated_at',
        ],
        'rows': mpesa_rows,
    },
    'inventory_movements': {
        'filename': 'inventory_movements.xlsx',
        'sheet': 'Inventory Movements',
        'headers': [
            'id', 'product', 'movement_type', 'quantity', 'previous_quantity', 'new_quantity',
            'reference', 'actor', 'note', 'created_at',
        ],
        'rows': movement_rows,
    },
}


def sync_excel_export(export_name):
    config = EXPORTS[export_name]
    return write_workbook(config['filename'], config['sheet'], config['headers'], config['rows']())


def sync_all_excel_exports():
    return {name: str(sync_excel_export(name)) for name in EXPORTS}


def export_status():
    status = []
    for name, config in EXPORTS.items():
        path = EXPORT_DIR / config['filename']
        status.append({
            'name': name,
            'filename': config['filename'],
            'path': str(path),
            'exists': path.exists(),
            'updated_at': (
                timezone.datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone())
                if path.exists()
                else None
            ),
        })
    return status


def schedule_sync(*export_names):
    if not AUTO_SYNC_ENABLED:
        return

    names = set(export_names)

    def run_sync():
        for name in names:
            sync_excel_export(name)

    transaction.on_commit(run_sync)


@receiver([post_save, post_delete], sender=Product)
def sync_products(sender, **kwargs):
    schedule_sync('products')


@receiver([post_save, post_delete], sender=Sale)
def sync_sales(sender, **kwargs):
    schedule_sync('sales')


@receiver([post_save, post_delete], sender=Customer)
def sync_customers(sender, **kwargs):
    schedule_sync('customers')


@receiver([post_save, post_delete], sender=Supplier)
def sync_suppliers(sender, **kwargs):
    schedule_sync('suppliers', 'products')


@receiver([post_save, post_delete], sender=Payment)
def sync_payments(sender, **kwargs):
    schedule_sync('payments')


@receiver([post_save, post_delete], sender=MpesaTransaction)
def sync_mpesa(sender, **kwargs):
    schedule_sync('mpesa')


@receiver([post_save, post_delete], sender=InventoryMovement)
def sync_inventory_movements(sender, **kwargs):
    schedule_sync('inventory_movements', 'products')
