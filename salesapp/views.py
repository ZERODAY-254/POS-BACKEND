from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import RolePermission
from audit.models import AuditLog
from customers.models import Customer
from payments.models import MpesaTransaction, Payment, PaymentNotification
from payments.mpesa import format_phone_number, send_stk_push
from products.models import InventoryMovement, Product
from returns.models import Return

from .models import Sale
from .serializers import SaleSerializer


class SaleViewSet(viewsets.ModelViewSet):
    allowed_roles = ('admin', 'manager', 'cashier')
    permission_classes = [RolePermission]

    queryset = Sale.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = SaleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'receipt_number', 'payment_reference']
    ordering_fields = ['created_at', 'amount', 'customer_name']

    def create(self, request, *args, **kwargs):
        items = request.data.get('items', [])
        payment_method = request.data.get('payment_method', 'cash')
        amount_paid = Decimal(str(request.data.get('amount_paid', request.data.get('grand_total', 0)) or 0))
        grand_total = Decimal(str(request.data.get('grand_total', request.data.get('amount', 0)) or 0))
        mpesa_phone = request.data.get('mpesa_phone', '').strip()

        if not items:
            return Response({
                'success': False,
                'message': 'Add at least one product before completing a sale.'
            }, status=status.HTTP_400_BAD_REQUEST)

        product_ids = [item.get('product_id') for item in items if item.get('product_id')]
        products = {
            product.id: product
            for product in Product.objects.filter(id__in=product_ids, is_active=True)
        }

        checked_items = []
        cost_total = Decimal('0')
        calculated_subtotal = Decimal('0')
        calculated_tax = Decimal('0')
        for item in items:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity') or 0)
            unit_id = item.get('unit_id')
            price_type = item.get('price_type', 'retail')
            product = products.get(product_id)

            if not product:
                return Response({
                    'success': False,
                    'message': f'Product {product_id} was not found or is inactive.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if quantity <= 0:
                return Response({
                    'success': False,
                    'message': f'Quantity for {product.name} must be at least 1.'
                }, status=status.HTTP_400_BAD_REQUEST)

            unit_ratio = int(product.unit_ratio(unit_id))
            base_quantity = quantity * unit_ratio
            unit_price = Decimal(product.selling_price_for(unit_id, price_type))
            line_subtotal = unit_price * quantity
            line_tax = Decimal(product.tax_amount_for(line_subtotal))

            if product.quantity < base_quantity:
                return Response({
                    'success': False,
                    'message': f'Not enough stock for {product.name}. Available base units: {product.quantity}.'
                }, status=status.HTTP_400_BAD_REQUEST)

            checked_items.append({
                'product': product,
                'quantity': quantity,
                'base_quantity': base_quantity,
                'receipt_item': {
                    'product_id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'barcode': product.barcode,
                    'unit_id': unit_id,
                    'unit_ratio': unit_ratio,
                    'price_type': price_type,
                    'price': float(unit_price),
                    'cost_price': float(product.cost_price),
                    'quantity': quantity,
                    'base_quantity': base_quantity,
                    'tax_rate': float(product.tax_code.rate) if product.tax_code else 0,
                    'tax_amount': float(line_tax),
                    'line_total': float(line_subtotal + line_tax),
                }
            })
            cost_total += Decimal(product.cost_price or 0) * base_quantity
            calculated_subtotal += line_subtotal
            calculated_tax += line_tax

        if not grand_total:
            grand_total = calculated_subtotal - Decimal(str(request.data.get('discount', 0) or 0)) + calculated_tax

        if payment_method == 'cash' and amount_paid < grand_total:
            return Response({
                'success': False,
                'message': 'Cash received is less than the sale total.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if payment_method == 'mpesa' and not mpesa_phone:
            return Response({
                'success': False,
                'message': 'Enter customer M-Pesa phone number.'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            mutable_data = request.data.copy()
            mutable_data['items'] = [item['receipt_item'] for item in checked_items]
            mutable_data['subtotal'] = request.data.get('subtotal') or calculated_subtotal
            mutable_data['tax'] = request.data.get('tax') or calculated_tax
            mutable_data['grand_total'] = grand_total
            mutable_data['payment_method'] = payment_method
            mutable_data['payment_status'] = 'pending' if payment_method == 'mpesa' else 'paid'
            mutable_data['amount_paid'] = amount_paid
            mutable_data['mpesa_phone'] = format_phone_number(mpesa_phone) if mpesa_phone else ''
            mutable_data['cost_total'] = cost_total
            mutable_data['profit'] = grand_total - cost_total

            serializer = self.get_serializer(data=mutable_data)
            serializer.is_valid(raise_exception=True)
            sale = serializer.save()

            for item in checked_items:
                product = item['product']
                previous_quantity = product.quantity
                product.quantity -= item['base_quantity']
                product.save(update_fields=['quantity'])
                InventoryMovement.objects.create(
                    product=product,
                    movement_type='sale',
                    quantity=item['base_quantity'],
                    previous_quantity=previous_quantity,
                    new_quantity=product.quantity,
                    reference=sale.receipt_number,
                    note=f'Sale to {sale.customer_name}',
                    actor=getattr(self.request.user, 'username', '') if self.request.user.is_authenticated else 'frontend',
                )
                if product.is_low_stock:
                    PaymentNotification.objects.create(
                        channel='inventory',
                        severity='warning',
                        title='Low stock alert',
                        message=f'{product.name} stock is {product.quantity}. Minimum is {product.minimum_stock}.',
                        action_url='/inventory',
                    )

            payment = Payment.objects.create(
                customer_name=sale.customer_name,
                amount=sale.grand_total,
                amount_received=sale.amount_paid if payment_method == 'cash' else sale.grand_total,
                method=payment_method if payment_method != 'mixed' else 'cash',
                status=sale.payment_status,
                reference=sale.receipt_number,
                mpesa_phone=sale.mpesa_phone,
            )

            if payment_method == 'mpesa':
                mpesa_transaction = MpesaTransaction.objects.create(
                    payment=payment,
                    phone_number=sale.mpesa_phone,
                    amount=sale.grand_total,
                    account_reference=sale.receipt_number,
                    status='pending',
                    raw_request={
                        'environment': settings.MPESA_ENVIRONMENT,
                        'callback_url': settings.MPESA_CALLBACK_URL,
                        'demo_mode': settings.MPESA_DEMO_MODE,
                    },
                )

                if settings.MPESA_DEMO_MODE:
                    mpesa_transaction.checkout_request_id = f'DEMO-SALE-{mpesa_transaction.id:06d}'
                    mpesa_transaction.merchant_request_id = f'MERCHANT-SALE-{mpesa_transaction.id:06d}'
                    mpesa_transaction.save(update_fields=['checkout_request_id', 'merchant_request_id'])
                else:
                    mpesa_response = send_stk_push(
                        phone_number=sale.mpesa_phone,
                        amount=sale.grand_total,
                        account_reference=sale.receipt_number,
                        transaction_description=f'Sale {sale.receipt_number}',
                    )
                    mpesa_transaction.raw_request = {
                        **mpesa_transaction.raw_request,
                        'daraja_response': mpesa_response.get('raw', {}),
                    }
                    mpesa_transaction.merchant_request_id = mpesa_response.get('merchant_request_id', '')
                    mpesa_transaction.checkout_request_id = mpesa_response.get('checkout_request_id', '') or None
                    if not mpesa_response.get('success'):
                        mpesa_transaction.status = 'failed'
                        mpesa_transaction.result_description = mpesa_response.get('message', 'M-Pesa request failed')
                        payment.status = 'failed'
                        sale.payment_status = 'failed'
                        payment.save(update_fields=['status'])
                        sale.save(update_fields=['payment_status'])
                    mpesa_transaction.save()

                PaymentNotification.objects.create(
                    channel='mpesa',
                    title='M-Pesa sale prompt sent',
                    message=f'Sale {sale.receipt_number} prompt sent to {sale.mpesa_phone}.',
                    payment=payment,
                    mpesa_transaction=mpesa_transaction,
                )

            AuditLog.objects.create(
                actor=getattr(self.request.user, 'username', '') if self.request.user.is_authenticated else 'frontend',
                action='Created sale',
                module='Sales',
                details=f'{sale.receipt_number} for {sale.customer_name}'
            )
            PaymentNotification.objects.create(
                channel='sales',
                severity='success',
                title='Sale completed',
                message=f'{sale.receipt_number} created for {sale.customer_name}.',
                action_url=f'/sales/{sale.id}',
            )

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        sale = self.get_object()
        return Response({
            'receipt_number': sale.receipt_number,
            'customer_name': sale.customer_name,
            'created_at': sale.created_at,
            'items': sale.items,
            'subtotal': sale.subtotal,
            'discount': sale.discount,
            'tax': sale.tax,
            'grand_total': sale.grand_total,
            'amount_paid': sale.amount_paid,
            'change_due': sale.change_due,
            'payment_method': sale.payment_method,
            'payment_status': sale.payment_status,
        })

    @action(detail=True, methods=['get'], url_path='print-receipt')
    def print_receipt(self, request, pk=None):
        sale = self.get_object()
        rows = ''.join(
            f'<tr><td>{item.get("name", "")}</td><td>{item.get("quantity", 0)}</td><td>{item.get("price", 0)}</td></tr>'
            for item in sale.items
        )
        html = f'''
        <html>
            <head><title>Receipt {sale.receipt_number}</title></head>
            <body>
                <h2>Receipt {sale.receipt_number}</h2>
                <p><strong>Customer:</strong> {sale.customer_name}</p>
                <p><strong>Date:</strong> {sale.created_at}</p>
                <table border="1" cellspacing="0" cellpadding="6">
                    <thead><tr><th>Item</th><th>Qty</th><th>Price</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                <p><strong>Subtotal:</strong> KES {sale.subtotal}</p>
                <p><strong>Discount:</strong> KES {sale.discount}</p>
                <p><strong>Tax:</strong> KES {sale.tax}</p>
                <h3>Total: KES {sale.grand_total}</h3>
                <p><strong>Paid:</strong> KES {sale.amount_paid}</p>
                <p><strong>Change:</strong> KES {sale.change_due}</p>
                <p><strong>Payment:</strong> {sale.payment_method} - {sale.payment_status}</p>
            </body>
        </html>
        '''
        return HttpResponse(html, content_type='text/html')

    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        sale = self.get_object()
        return Response({
            'invoice_number': sale.invoice_number,
            'receipt_number': sale.receipt_number,
            'customer_name': sale.customer_name,
            'created_at': sale.created_at,
            'items': sale.items,
            'subtotal': sale.subtotal,
            'discount': sale.discount,
            'tax': sale.tax,
            'grand_total': sale.grand_total,
            'payment_status': sale.payment_status,
        })

    @action(detail=True, methods=['get'], url_path='print-invoice')
    def print_invoice(self, request, pk=None):
        sale = self.get_object()
        rows = ''.join(
            f'<tr><td>{item.get("name", "")}</td><td>{item.get("quantity", 0)}</td><td>{item.get("price", 0)}</td></tr>'
            for item in sale.items
        )
        html = f'''
        <html>
            <head><title>Invoice {sale.invoice_number}</title></head>
            <body>
                <h2>Invoice {sale.invoice_number}</h2>
                <p><strong>Receipt:</strong> {sale.receipt_number}</p>
                <p><strong>Customer:</strong> {sale.customer_name}</p>
                <p><strong>Date:</strong> {sale.created_at}</p>
                <table border="1" cellspacing="0" cellpadding="6">
                    <thead><tr><th>Item</th><th>Qty</th><th>Unit Price</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                <p><strong>Subtotal:</strong> KES {sale.subtotal}</p>
                <p><strong>Discount:</strong> KES {sale.discount}</p>
                <p><strong>Tax:</strong> KES {sale.tax}</p>
                <h3>Amount Due: KES {sale.grand_total}</h3>
                <p><strong>Status:</strong> {sale.payment_status}</p>
            </body>
        </html>
        '''
        return HttpResponse(html, content_type='text/html')

    @action(detail=False, methods=['get'], url_path='daily-report')
    def daily_report(self, request):
        date_text = request.query_params.get('date')
        report_date = timezone.localdate()
        if date_text:
            report_date = timezone.datetime.fromisoformat(date_text).date()

        sales = self.get_queryset().filter(created_at__date=report_date)
        totals = sales.aggregate(
            total_sales=Sum('grand_total'),
            total_profit=Sum('profit'),
            transactions=Count('id'),
        )
        return Response({
            'date': report_date,
            'total_sales': totals['total_sales'] or Decimal('0'),
            'total_profit': totals['total_profit'] or Decimal('0'),
            'transactions': totals['transactions'] or 0,
            'sales': SaleSerializer(sales, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        sales = self.get_queryset()
        today_sales = sales.filter(created_at__date=today)
        month_sales = sales.filter(created_at__date__gte=month_start)
        returns = Return.objects.filter(is_active=True)
        today_returns = returns.filter(returned_at__date=today)
        month_returns = returns.filter(returned_at__date__gte=month_start)
        totals = sales.aggregate(
            total_sales=Sum('grand_total'),
            total_profit=Sum('profit'),
            transactions=Count('id'),
        )
        today_totals = today_sales.aggregate(
            revenue=Sum('grand_total'),
            transactions=Count('id'),
        )
        month_totals = month_sales.aggregate(
            revenue=Sum('grand_total'),
            transactions=Count('id'),
        )
        daily = (
            sales.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Sum('grand_total'), profit=Sum('profit'), count=Count('id'))
            .order_by('-day')[:14]
        )

        top_products = {}
        today_items_sold = 0
        for sale in sales[:500]:
            for item in sale.items:
                name = item.get('name', 'Unknown')
                quantity = int(item.get('quantity') or 0)
                amount = Decimal(str(item.get('price') or 0)) * quantity
                current = top_products.setdefault(name, {'name': name, 'quantity': 0, 'sales': Decimal('0')})
                current['quantity'] += quantity
                current['sales'] += amount
                if sale.created_at.date() == today:
                    today_items_sold += quantity

        payment_methods = (
            sales.values('payment_method')
            .annotate(total=Sum('grand_total'), count=Count('id'))
            .order_by('-total')
        )

        month_revenue = month_totals['revenue'] or Decimal('0')
        avg_transaction = (
            (today_totals['revenue'] or Decimal('0')) / today_totals['transactions']
            if today_totals['transactions']
            else Decimal('0')
        )

        return Response({
            'total_sales': totals['total_sales'] or Decimal('0'),
            'total_profit': totals['total_profit'] or Decimal('0'),
            'transactions': totals['transactions'] or 0,
            'today_sales': today_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0'),
            'daily_sales': list(daily),
            'top_products': sorted(top_products.values(), key=lambda item: item['sales'], reverse=True)[:10],
            'today': {
                'revenue': today_totals['revenue'] or Decimal('0'),
                'transactions': today_totals['transactions'] or 0,
                'items_sold': today_items_sold,
                'avg_transaction': avg_transaction,
                'returns': today_returns.count(),
            },
            'this_month': {
                'revenue': month_revenue,
                'transactions': month_totals['transactions'] or 0,
                'returns': month_returns.count(),
                'return_amount': month_returns.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            },
            'growth': {
                'revenue_percentage': 0,
                'vs_last_month': Decimal('0'),
            },
            'payment_methods': [
                {
                    'method': row['payment_method'] or 'unknown',
                    'total': row['total'] or Decimal('0'),
                    'count': row['count'],
                }
                for row in payment_methods
            ],
            'recent_sales': SaleSerializer(sales[:10], many=True, context={'request': request}).data,
            'metrics': {
                'total_customers': Customer.objects.filter(is_active=True).count(),
                'total_products': Product.objects.filter(is_active=True).count(),
                'low_stock_products': Product.objects.filter(is_active=True, quantity__lte=F('minimum_stock')).count(),
            },
        })

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        AuditLog.objects.create(
            actor=getattr(self.request.user, 'username', '') if self.request.user.is_authenticated else 'frontend',
            action='Deactivated sale',
            module='Sales',
            details=f'{instance.receipt_number} for {instance.customer_name}'
        )
