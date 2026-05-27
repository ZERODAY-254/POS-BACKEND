from django.db import models
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Category, InventoryMovement, Product, ProductUnit, ProductUnitConversion, Supplier, TaxCode
from .serializers import (
    CategorySerializer,
    InventoryMovementSerializer,
    ProductSerializer,
    ProductUnitConversionSerializer,
    ProductUnitSerializer,
    SupplierSerializer,
    TaxCodeSerializer,
)
from audit.models import AuditLog
from accounts.permissions import IsInventoryStaff
from payments.models import PaymentNotification


@api_view(['GET', 'POST'])
@permission_classes([IsInventoryStaff])
def product_list(request):
    if request.method == 'POST':
        return create_product_response(request)

    products = Product.objects.filter(is_active=True).order_by('-created_at')
    search = request.query_params.get('search')

    if search:
        products = (
            products.filter(name__icontains=search) |
            products.filter(sku__icontains=search) |
            products.filter(barcode__icontains=search)
        )

    serializer = ProductSerializer(products, many=True)

    return Response(serializer.data)


def create_product_response(request):
    serializer = ProductSerializer(data=request.data)

    if serializer.is_valid():
        product = serializer.save()
        AuditLog.objects.create(action='Created product', module='Products', actor='frontend', details=product.name)

        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsInventoryStaff])
def product_detail(request, product_id):
    if request.method == 'GET':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        return Response(ProductSerializer(product).data)

    if request.method == 'PUT':
        return update_product(request, product_id)

    return delete_product(request, product_id)


@api_view(['POST'])
@permission_classes([IsInventoryStaff])
def add_product(request):
    return create_product_response(request)


@api_view(['PUT'])
@permission_classes([IsInventoryStaff])
def update_product(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    serializer = ProductSerializer(
        product,
        data=request.data
    )

    if serializer.is_valid():
        product = serializer.save()
        AuditLog.objects.create(action='Updated product', module='Products', actor='frontend', details=product.name)

        return Response({
            'success': True,
            'data': serializer.data
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsInventoryStaff])
def delete_product(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    product.is_active = False
    product.save(update_fields=['is_active'])
    AuditLog.objects.create(action='Deactivated product', module='Products', actor='frontend', details=product.name)

    return Response({
        'success': True,
        'message': 'Product deactivated'
    })


@api_view(['GET', 'POST'])
@permission_classes([IsInventoryStaff])
def category_list(request):
    if request.method == 'GET':
        categories = Category.objects.filter(is_active=True).order_by('name')
        return Response(CategorySerializer(categories, many=True).data)

    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsInventoryStaff])
def supplier_list(request):
    if request.method == 'GET':
        suppliers = Supplier.objects.filter(is_active=True).order_by('name')
        return Response(SupplierSerializer(suppliers, many=True).data)

    serializer = SupplierSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsInventoryStaff])
def unit_list(request):
    if request.method == 'GET':
        units = ProductUnit.objects.filter(is_active=True).order_by('name')
        return Response(ProductUnitSerializer(units, many=True).data)

    serializer = ProductUnitSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsInventoryStaff])
def tax_code_list(request):
    if request.method == 'GET':
        taxes = TaxCode.objects.filter(is_active=True).order_by('code')
        return Response(TaxCodeSerializer(taxes, many=True).data)

    serializer = TaxCodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsInventoryStaff])
def unit_conversions(request):
    if request.method == 'GET':
        conversions = ProductUnitConversion.objects.select_related('product', 'unit').filter(is_active=True)
        product_id = request.query_params.get('product_id')
        if product_id:
            conversions = conversions.filter(product_id=product_id)
        return Response(ProductUnitConversionSerializer(conversions, many=True).data)

    serializer = ProductUnitConversionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsInventoryStaff])
def conversion_preview(request):
    product = get_object_or_404(Product, id=request.query_params.get('product_id'), is_active=True)
    unit_id = request.query_params.get('unit_id')
    quantity = int(request.query_params.get('quantity') or 1)
    price_type = request.query_params.get('price_type', 'retail')
    ratio = product.unit_ratio(unit_id)
    base_quantity = ratio * quantity
    unit_price = product.selling_price_for(unit_id, price_type)
    subtotal = unit_price * quantity
    tax_amount = product.tax_amount_for(subtotal)

    return Response({
        'product_id': product.id,
        'quantity': quantity,
        'unit_id': unit_id,
        'base_quantity': base_quantity,
        'unit_price': unit_price,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total': subtotal + tax_amount,
    })


@api_view(['GET'])
@permission_classes([IsInventoryStaff])
def stock_alerts(request):
    products = Product.objects.filter(is_active=True, quantity__lte=models.F('minimum_stock')).order_by('quantity')
    return Response(ProductSerializer(products, many=True).data)


@api_view(['GET'])
@permission_classes([IsInventoryStaff])
def inventory_movements(request):
    movements = InventoryMovement.objects.select_related('product').order_by('-created_at')
    product_id = request.query_params.get('product_id')
    movement_type = request.query_params.get('movement_type')

    if product_id:
        movements = movements.filter(product_id=product_id)

    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    return Response(InventoryMovementSerializer(movements[:200], many=True).data)


@api_view(['POST'])
@permission_classes([IsInventoryStaff])
def adjust_inventory(request):
    product = get_object_or_404(Product, id=request.data.get('product_id'), is_active=True)
    movement_type = request.data.get('movement_type', 'adjustment')
    quantity = int(request.data.get('quantity') or 0)
    note = request.data.get('note', '').strip()
    reference = request.data.get('reference', '').strip()

    if movement_type not in dict(InventoryMovement.MOVEMENT_TYPES):
        return Response({
            'success': False,
            'message': 'Invalid movement type'
        }, status=status.HTTP_400_BAD_REQUEST)

    if quantity <= 0:
        return Response({
            'success': False,
            'message': 'Quantity must be greater than zero'
        }, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        previous_quantity = product.quantity
        if movement_type in ['stock_in', 'return']:
            product.quantity += quantity
        elif movement_type in ['stock_out', 'sale', 'damage']:
            if product.quantity < quantity:
                return Response({
                    'success': False,
                    'message': f'Not enough stock. Available: {product.quantity}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            product.quantity -= quantity
        else:
            product.quantity = quantity

        product.save(update_fields=['quantity'])
        movement = InventoryMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=product.quantity,
            reference=reference,
            note=note,
            actor=getattr(request.user, 'username', 'system'),
        )
        AuditLog.objects.create(
            actor=getattr(request.user, 'username', 'system'),
            action='Adjusted inventory',
            module='Inventory',
            details=f'{product.name}: {previous_quantity} -> {product.quantity}'
        )

        if product.is_low_stock:
            PaymentNotification.objects.create(
                channel='inventory',
                severity='warning',
                title='Low stock alert',
                message=f'{product.name} stock is {product.quantity}. Minimum is {product.minimum_stock}.',
            )

    return Response({
        'success': True,
        'product': ProductSerializer(product).data,
        'movement': InventoryMovementSerializer(movement).data,
    })
