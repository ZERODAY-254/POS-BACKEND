from decimal import Decimal
import zipfile

from django.conf import settings
from django.http import FileResponse, Http404
from django.db import models
from django.http import HttpResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsReportsStaff, IsSalesStaff
from customers.models import Customer
from payments.models import MpesaTransaction, Payment, PaymentNotification
from products.models import Category, InventoryMovement, Product, ProductUnit, Supplier, TaxCode
from salesapp.models import Sale
from .models import ApprovalRequest, Branch, OfflineSyncLog, Terminal
from .serializers import ApprovalRequestSerializer, BranchSerializer, OfflineSyncLogSerializer, TerminalSerializer
from .excel import CONTENT_TYPE, build_xlsx, read_xlsx_rows
from .excel_sync import EXPORTS, export_status, sync_all_excel_exports, sync_excel_export


def parse_date_range(request):
    start_text = request.query_params.get('start')
    end_text = request.query_params.get('end')
    end_date = timezone.localdate()
    start_date = end_date.replace(day=1)

    if start_text:
        start_date = timezone.datetime.fromisoformat(start_text).date()

    if end_text:
        end_date = timezone.datetime.fromisoformat(end_text).date()

    return start_date, end_date


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def reports_summary(request):
    start_date, end_date = parse_date_range(request)
    sales = Sale.objects.filter(is_active=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
    payments = Payment.objects.filter(is_active=True, paid_at__date__gte=start_date, paid_at__date__lte=end_date)

    sales_totals = sales.aggregate(
        total_sales=Sum('grand_total'),
        total_profit=Sum('profit'),
        transactions=Count('id'),
    )
    payment_totals = payments.values('method').annotate(total=Sum('amount'), count=Count('id')).order_by('method')

    return Response({
        'start': start_date,
        'end': end_date,
        'total_sales': sales_totals['total_sales'] or Decimal('0'),
        'total_profit': sales_totals['total_profit'] or Decimal('0'),
        'transactions': sales_totals['transactions'] or 0,
        'payments_by_method': list(payment_totals),
        'low_stock_count': Product.objects.filter(is_active=True, quantity__lte=models.F('minimum_stock')).count(),
        'unread_notifications': PaymentNotification.objects.filter(is_read=False).count(),
        'pending_mpesa': MpesaTransaction.objects.filter(status='pending').count(),
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def sales_report(request):
    start_date, end_date = parse_date_range(request)
    sales = Sale.objects.filter(is_active=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
    daily = (
        sales.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('grand_total'), profit=Sum('profit'), count=Count('id'))
        .order_by('day')
    )

    return Response({
        'start': start_date,
        'end': end_date,
        'totals': sales.aggregate(total=Sum('grand_total'), profit=Sum('profit'), count=Count('id')),
        'daily': list(daily),
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def inventory_report(request):
    products = Product.objects.filter(is_active=True)
    low_stock = products.filter(quantity__lte=models.F('minimum_stock')).order_by('quantity')
    movements = InventoryMovement.objects.select_related('product').order_by('-created_at')[:100]

    stock_value = Decimal('0')
    cost_value = Decimal('0')
    for product in products:
        stock_value += Decimal(product.price or 0) * product.quantity
        cost_value += Decimal(product.cost_price or 0) * product.quantity

    return Response({
        'product_count': products.count(),
        'low_stock_count': low_stock.count(),
        'stock_value': stock_value,
        'cost_value': cost_value,
        'low_stock': [
            {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'quantity': product.quantity,
                'minimum_stock': product.minimum_stock,
            }
            for product in low_stock[:50]
        ],
        'recent_movements': [
            {
                'id': movement.id,
                'product': movement.product.name,
                'movement_type': movement.movement_type,
                'quantity': movement.quantity,
                'previous_quantity': movement.previous_quantity,
                'new_quantity': movement.new_quantity,
                'created_at': movement.created_at,
            }
            for movement in movements
        ],
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def payments_report(request):
    start_date, end_date = parse_date_range(request)
    payments = Payment.objects.filter(is_active=True, paid_at__date__gte=start_date, paid_at__date__lte=end_date)
    mpesa = MpesaTransaction.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    return Response({
        'start': start_date,
        'end': end_date,
        'payments_by_method': list(payments.values('method').annotate(total=Sum('amount'), count=Count('id')).order_by('method')),
        'payments_by_status': list(payments.values('status').annotate(total=Sum('amount'), count=Count('id')).order_by('status')),
        'mpesa_by_status': list(mpesa.values('status').annotate(total=Sum('amount'), count=Count('id')).order_by('status')),
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def dashboard_charts(request):
    start_date, end_date = parse_date_range(request)
    sales = Sale.objects.filter(is_active=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
    payments = Payment.objects.filter(is_active=True, paid_at__date__gte=start_date, paid_at__date__lte=end_date)

    daily_sales = (
        sales.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('grand_total'), profit=Sum('profit'), count=Count('id'))
        .order_by('day')
    )
    payment_methods = payments.values('method').annotate(total=Sum('amount'), count=Count('id')).order_by('method')

    top_products = {}
    for sale in sales[:1000]:
        for item in sale.items:
            name = item.get('name', 'Unknown')
            quantity = int(item.get('quantity') or 0)
            amount = Decimal(str(item.get('price') or 0)) * quantity
            current = top_products.setdefault(name, {'label': name, 'quantity': 0, 'value': Decimal('0')})
            current['quantity'] += quantity
            current['value'] += amount

    low_stock = Product.objects.filter(is_active=True, quantity__lte=models.F('minimum_stock')).order_by('quantity')[:20]

    return Response({
        'daily_sales': [
            {
                'label': row['day'],
                'sales': row['total'] or Decimal('0'),
                'profit': row['profit'] or Decimal('0'),
                'transactions': row['count'],
            }
            for row in daily_sales
        ],
        'payment_methods': [
            {'label': row['method'], 'value': row['total'] or Decimal('0'), 'count': row['count']}
            for row in payment_methods
        ],
        'top_products': sorted(top_products.values(), key=lambda item: item['value'], reverse=True)[:10],
        'low_stock': [
            {'label': product.name, 'quantity': product.quantity, 'minimum_stock': product.minimum_stock}
            for product in low_stock
        ],
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def dashboard_statistics(request):
    start_date, end_date = parse_date_range(request)
    sales = Sale.objects.filter(is_active=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
    payments = Payment.objects.filter(is_active=True, paid_at__date__gte=start_date, paid_at__date__lte=end_date)
    sales_totals = sales.aggregate(total=Sum('grand_total'), profit=Sum('profit'), count=Count('id'))

    return Response({
        'total_sales': sales_totals['total'] or Decimal('0'),
        'total_profit': sales_totals['profit'] or Decimal('0'),
        'transactions': sales_totals['count'] or 0,
        'payment_total': payments.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
        'product_count': Product.objects.filter(is_active=True).count(),
        'customer_count': Customer.objects.filter(is_active=True).count(),
        'low_stock_count': Product.objects.filter(is_active=True, quantity__lte=models.F('minimum_stock')).count(),
        'pending_mpesa': MpesaTransaction.objects.filter(status='pending').count(),
        'unread_notifications': PaymentNotification.objects.filter(is_read=False).count(),
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def reports_daily_summary(request):
    date_text = request.query_params.get('date')
    report_date = timezone.datetime.fromisoformat(date_text).date() if date_text else timezone.localdate()
    sales = Sale.objects.filter(is_active=True, created_at__date=report_date)
    payments = Payment.objects.filter(is_active=True, paid_at__date=report_date)

    return Response({
        'date': report_date,
        'sales': sales.aggregate(total=Sum('grand_total'), profit=Sum('profit'), count=Count('id')),
        'payments': list(payments.values('method').annotate(total=Sum('amount'), count=Count('id')).order_by('method')),
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def reports_transaction_history(request):
    limit = int(request.query_params.get('limit', 100))
    sales = Sale.objects.filter(is_active=True).order_by('-created_at')[:limit]

    return Response([
        {
            'id': sale.id,
            'receipt_number': sale.receipt_number,
            'invoice_number': sale.invoice_number,
            'customer_name': sale.customer_name,
            'grand_total': sale.grand_total,
            'payment_method': sale.payment_method,
            'payment_status': sale.payment_status,
            'created_at': sale.created_at,
        }
        for sale in sales
    ])


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def reports_top_products(request):
    start_date, end_date = parse_date_range(request)
    sales = Sale.objects.filter(is_active=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
    top_products = {}

    for sale in sales[:1000]:
        for item in sale.items:
            name = item.get('name', 'Unknown')
            quantity = int(item.get('quantity') or 0)
            amount = Decimal(str(item.get('price') or 0)) * quantity
            current = top_products.setdefault(name, {'name': name, 'quantity': 0, 'total': Decimal('0')})
            current['quantity'] += quantity
            current['total'] += amount

    return Response(sorted(top_products.values(), key=lambda item: item['total'], reverse=True)[:20])


@api_view(['GET'])
@permission_classes([IsSalesStaff])
def react_payment_config(request):
    return Response({
        'stk_push_url': '/api/mpesa-transactions/stk-push/',
        'transactions_url': '/api/mpesa-transactions/',
        'payments_url': '/api/payments/',
        'callback_config_url': '/api/mpesa/callback-config/',
        'supported_methods': ['cash', 'mpesa', 'card', 'bank', 'mixed'],
    })


@api_view(['GET', 'POST'])
@permission_classes([IsReportsStaff])
def branches(request):
    if request.method == 'GET':
        queryset = Branch.objects.filter(is_active=True).order_by('name')
        return Response(BranchSerializer(queryset, many=True).data)

    serializer = BranchSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsReportsStaff])
def terminals(request):
    if request.method == 'GET':
        queryset = Terminal.objects.select_related('branch').filter(is_active=True).order_by('branch__name', 'name')
        return Response(TerminalSerializer(queryset, many=True).data)

    serializer = TerminalSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsSalesStaff])
def terminal_heartbeat(request):
    terminal = Terminal.objects.filter(terminal_code=request.data.get('terminal_code')).first()
    if not terminal:
        return Response({'success': False, 'message': 'Terminal not found'}, status=status.HTTP_404_NOT_FOUND)

    terminal.status = 'online'
    terminal.ip_address = request.META.get('REMOTE_ADDR')
    terminal.last_seen_at = timezone.now()
    terminal.save(update_fields=['status', 'ip_address', 'last_seen_at'])
    return Response({'success': True, 'terminal': TerminalSerializer(terminal).data})


@api_view(['GET', 'POST'])
@permission_classes([IsSalesStaff])
def approval_requests(request):
    if request.method == 'GET':
        queryset = ApprovalRequest.objects.order_by('-created_at')
        request_status = request.query_params.get('status')
        if request_status:
            queryset = queryset.filter(status=request_status)
        return Response(ApprovalRequestSerializer(queryset[:200], many=True).data)

    serializer = ApprovalRequestSerializer(data={
        **request.data,
        'requested_by': getattr(request.user, 'username', ''),
    })
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsReportsStaff])
def decide_approval(request, approval_id):
    approval = ApprovalRequest.objects.filter(id=approval_id).first()
    if not approval:
        return Response({'success': False, 'message': 'Approval request not found'}, status=status.HTTP_404_NOT_FOUND)

    decision = request.data.get('status')
    if decision not in ['approved', 'rejected', 'held']:
        return Response({'success': False, 'message': 'Decision must be approved, rejected, or held'}, status=status.HTTP_400_BAD_REQUEST)

    approval.status = decision
    approval.approved_by = getattr(request.user, 'username', '')
    approval.decision_note = request.data.get('decision_note', '')
    approval.decided_at = timezone.now()
    approval.save(update_fields=['status', 'approved_by', 'decision_note', 'decided_at'])
    return Response({'success': True, 'data': ApprovalRequestSerializer(approval).data})


@api_view(['GET', 'POST'])
@permission_classes([IsSalesStaff])
def offline_sync_logs(request):
    if request.method == 'GET':
        queryset = OfflineSyncLog.objects.select_related('terminal').order_by('-created_at')
        sync_status = request.query_params.get('status')
        if sync_status:
            queryset = queryset.filter(status=sync_status)
        return Response(OfflineSyncLogSerializer(queryset[:200], many=True).data)

    serializer = OfflineSyncLogSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def excel_response(filename, sheet_name, headers, rows):
    response = HttpResponse(build_xlsx(sheet_name, headers, rows), content_type=CONTENT_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def automatic_excel_status(request):
    return Response({
        'auto_sync_enabled': settings.EXCEL_AUTO_SYNC_ENABLED,
        'exports': export_status(),
        'download_url_pattern': '/api/excel/automatic/<name>/download/',
        'rebuild_url': '/api/excel/automatic/rebuild/',
    })


@api_view(['POST'])
@permission_classes([IsReportsStaff])
def rebuild_automatic_excel(request):
    export_name = request.data.get('name')
    if export_name:
        if export_name not in EXPORTS:
            return Response({
                'success': False,
                'message': f'Unknown export "{export_name}"',
                'available_exports': sorted(EXPORTS.keys()),
            }, status=status.HTTP_400_BAD_REQUEST)
        paths = {export_name: str(sync_excel_export(export_name))}
    else:
        paths = sync_all_excel_exports()

    return Response({
        'success': True,
        'exports': paths,
    })


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def download_automatic_excel(request, name):
    if name not in EXPORTS:
        raise Http404('Unknown Excel export')

    path = sync_excel_export(name)
    return FileResponse(
        open(path, 'rb'),
        as_attachment=True,
        filename=EXPORTS[name]['filename'],
        content_type=CONTENT_TYPE,
    )


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def excel_template(request):
    headers = [
        'name',
        'sku',
        'barcode',
        'category',
        'supplier',
        'base_unit',
        'tax_code',
        'cost_price',
        'retail_price',
        'wholesale_price',
        'quantity',
        'minimum_stock',
        'description',
    ]
    rows = [[
        'Example Product',
        'SKU-001',
        '123456789',
        'General',
        'Default Supplier',
        'Piece',
        'VAT16',
        80,
        100,
        90,
        24,
        5,
        'Sample row. Delete or edit before import.',
    ]]
    return excel_response('product_import_template.xlsx', 'Products', headers, rows)


@api_view(['GET'])
@permission_classes([IsReportsStaff])
def excel_export(request, export_type):
    export_type = export_type.lower()

    if export_type == 'products':
        headers = ['id', 'name', 'sku', 'barcode', 'category', 'supplier', 'base_unit', 'tax_code', 'cost_price', 'retail_price', 'wholesale_price', 'quantity', 'minimum_stock']
        rows = [
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
            ]
            for product in Product.objects.select_related('category', 'supplier', 'base_unit', 'tax_code').filter(is_active=True)
        ]
        return excel_response('products.xlsx', 'Products', headers, rows)

    if export_type == 'inventory':
        headers = ['product', 'sku', 'movement_type', 'quantity', 'previous_quantity', 'new_quantity', 'reference', 'actor', 'created_at']
        rows = [
            [movement.product.name, movement.product.sku, movement.movement_type, movement.quantity, movement.previous_quantity, movement.new_quantity, movement.reference, movement.actor, movement.created_at]
            for movement in InventoryMovement.objects.select_related('product').order_by('-created_at')[:1000]
        ]
        return excel_response('inventory_movements.xlsx', 'Inventory', headers, rows)

    if export_type == 'sales':
        headers = ['receipt_number', 'invoice_number', 'customer_name', 'subtotal', 'tax', 'discount', 'grand_total', 'profit', 'payment_method', 'payment_status', 'created_at']
        rows = [
            [sale.receipt_number, sale.invoice_number, sale.customer_name, sale.subtotal, sale.tax, sale.discount, sale.grand_total, sale.profit, sale.payment_method, sale.payment_status, sale.created_at]
            for sale in Sale.objects.filter(is_active=True).order_by('-created_at')[:1000]
        ]
        return excel_response('sales.xlsx', 'Sales', headers, rows)

    return Response({'success': False, 'message': 'Export type must be products, inventory, or sales'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsReportsStaff])
def excel_import_products(request):
    upload = request.FILES.get('file')
    if not upload:
        return Response({'success': False, 'message': 'Upload an Excel file using the field name file'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rows = read_xlsx_rows(upload)
    except (zipfile.BadZipFile, KeyError, ValueError) as error:
        return Response({'success': False, 'message': f'Invalid Excel file: {error}'}, status=status.HTTP_400_BAD_REQUEST)

    if not rows:
        return Response({'success': False, 'message': 'Excel file is empty'}, status=status.HTTP_400_BAD_REQUEST)

    headers = [str(value).strip().lower() for value in rows[0]]
    created = 0
    updated = 0
    errors = []

    def value(data, key, default=''):
        try:
            return data[headers.index(key)]
        except ValueError:
            return default

    for row_number, row in enumerate(rows[1:], start=2):
        data = row + [''] * (len(headers) - len(row))
        name = str(value(data, 'name')).strip()
        if not name:
            continue

        try:
            category_name = str(value(data, 'category')).strip()
            supplier_name = str(value(data, 'supplier')).strip()
            unit_name = str(value(data, 'base_unit')).strip()
            tax_code_value = str(value(data, 'tax_code')).strip()

            category = Category.objects.get_or_create(name=category_name)[0] if category_name else None
            supplier = Supplier.objects.get_or_create(name=supplier_name)[0] if supplier_name else None
            base_unit = ProductUnit.objects.get_or_create(name=unit_name)[0] if unit_name else None
            tax_code = TaxCode.objects.filter(code=tax_code_value).first() if tax_code_value else None

            sku = str(value(data, 'sku')).strip()
            product, was_created = Product.objects.update_or_create(
                sku=sku or None,
                defaults={
                    'name': name,
                    'barcode': str(value(data, 'barcode')).strip(),
                    'category': category,
                    'supplier': supplier,
                    'base_unit': base_unit,
                    'tax_code': tax_code,
                    'cost_price': Decimal(str(value(data, 'cost_price', 0) or 0)),
                    'price': Decimal(str(value(data, 'retail_price', 0) or 0)),
                    'wholesale_price': Decimal(str(value(data, 'wholesale_price', 0) or 0)),
                    'quantity': int(float(value(data, 'quantity', 0) or 0)),
                    'minimum_stock': int(float(value(data, 'minimum_stock', 5) or 5)),
                    'description': str(value(data, 'description')).strip(),
                    'is_active': True,
                },
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1
        except Exception as error:
            errors.append({'row': row_number, 'message': str(error)})

    return Response({
        'success': not errors,
        'created': created,
        'updated': updated,
        'errors': errors,
    })
