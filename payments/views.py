from decimal import Decimal

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import RolePermission
from .models import CashDrawer, CashDrawerTransaction, MpesaTransaction, Payment, PaymentNotification
from .serializers import (
    CashDrawerSerializer,
    CashDrawerTransactionSerializer,
    MpesaTransactionSerializer,
    PaymentNotificationSerializer,
    PaymentSerializer,
)
from .mpesa import format_phone_number, query_stk_status, send_stk_push
from .services import confirm_mpesa_transaction


class PaymentViewSet(viewsets.ModelViewSet):
    allowed_roles = ('admin', 'manager', 'cashier')
    permission_classes = [RolePermission]

    queryset = Payment.objects.filter(is_active=True).order_by('-paid_at')
    serializer_class = PaymentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'reference', 'mpesa_receipt', 'terminal_reference']
    ordering_fields = ['paid_at', 'amount', 'status', 'method']

    def perform_create(self, serializer):
        payment = serializer.save()
        if payment.method == 'cash':
            drawer = CashDrawer.objects.filter(status='open', is_active=True).order_by('-opened_at').first()
            if drawer:
                CashDrawerTransaction.objects.create(
                    drawer=drawer,
                    payment=payment,
                    transaction_type='sale',
                    amount=payment.amount_received,
                    note=f'Cash payment from {payment.customer_name}',
                )
                drawer.expected_balance += Decimal(payment.amount_received)
                drawer.save(update_fields=['expected_balance'])

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class MpesaTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    allowed_roles = ('admin', 'manager', 'cashier')
    permission_classes = [RolePermission]

    queryset = MpesaTransaction.objects.all().order_by('-created_at')
    serializer_class = MpesaTransactionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['phone_number', 'checkout_request_id', 'mpesa_receipt_number', 'account_reference']
    ordering_fields = ['created_at', 'amount', 'status']

    @action(detail=False, methods=['post'], url_path='stk-push')
    def stk_push(self, request):
        phone_number = request.data.get('phone_number', '').strip()
        amount = Decimal(str(request.data.get('amount', '0') or '0'))
        customer_name = request.data.get('customer_name', 'M-Pesa Customer').strip()
        account_reference = request.data.get('account_reference', 'POS-SALE').strip()

        if not phone_number or amount <= 0:
            return Response({
                'success': False,
                'message': 'Phone number and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        formatted_phone = format_phone_number(phone_number)

        payment = Payment.objects.create(
            customer_name=customer_name,
            amount=amount,
            amount_received=amount,
            method='mpesa',
            status='pending',
            reference=account_reference,
            mpesa_phone=formatted_phone,
        )

        transaction = MpesaTransaction.objects.create(
            payment=payment,
            phone_number=formatted_phone,
            amount=amount,
            account_reference=account_reference,
            status='pending',
            raw_request={
                'environment': settings.MPESA_ENVIRONMENT,
                'callback_url': settings.MPESA_CALLBACK_URL,
                'demo_mode': settings.MPESA_DEMO_MODE,
            },
        )

        if settings.MPESA_DEMO_MODE:
            transaction.checkout_request_id = f'DEMO-{transaction.id:06d}'
            transaction.merchant_request_id = f'MERCHANT-{transaction.id:06d}'
            transaction.save(update_fields=['checkout_request_id', 'merchant_request_id'])
        else:
            mpesa_response = send_stk_push(
                phone_number=formatted_phone,
                amount=amount,
                account_reference=account_reference,
                transaction_description=f'Payment from {customer_name}',
            )
            transaction.raw_request = {
                **transaction.raw_request,
                'daraja_response': mpesa_response.get('raw', {}),
            }
            transaction.merchant_request_id = mpesa_response.get('merchant_request_id', '')
            transaction.checkout_request_id = mpesa_response.get('checkout_request_id', '') or None
            if not mpesa_response.get('success'):
                transaction.status = 'failed'
                transaction.result_description = mpesa_response.get('message', 'M-Pesa request failed')
                payment.status = 'failed'
                payment.save(update_fields=['status'])
            transaction.save()

        PaymentNotification.objects.create(
            channel='mpesa',
            title='M-Pesa payment request sent',
            message=f'STK push request sent to {phone_number} for KES {amount}.',
            payment=payment,
            mpesa_transaction=transaction,
        )

        return Response({
            'success': transaction.status != 'failed',
            'demo_mode': settings.MPESA_DEMO_MODE,
            'message': transaction.result_description or 'M-Pesa payment request created',
            'transaction': MpesaTransactionSerializer(transaction).data,
        }, status=status.HTTP_201_CREATED if transaction.status != 'failed' else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        transaction = self.get_object()

        if settings.MPESA_DEMO_MODE:
            demo_status = request.data.get('status', 'success')
            transaction = confirm_mpesa_transaction(
                transaction=transaction,
                result_code='0' if demo_status == 'success' else '1',
                result_description='Demo verification completed',
                metadata={'MpesaReceiptNumber': f'DEMO-RCPT-{transaction.id:06d}'},
                raw_callback={'demo': True, 'verified_at': timezone.now().isoformat()},
            )
            return Response({
                'success': True,
                'demo_mode': True,
                'transaction': MpesaTransactionSerializer(transaction).data,
            })

        if not transaction.checkout_request_id:
            return Response({
                'success': False,
                'message': 'Transaction has no checkout request id'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = query_stk_status(transaction.checkout_request_id)
        transaction = confirm_mpesa_transaction(
            transaction=transaction,
            result_code=result.get('result_code', transaction.result_code or '1'),
            result_description=result.get('message', transaction.result_description),
            raw_callback={**transaction.raw_callback, 'verification': result.get('raw', {})},
        )

        return Response({
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'transaction': MpesaTransactionSerializer(transaction).data,
        })


class PaymentNotificationViewSet(viewsets.ModelViewSet):
    allowed_roles = ('admin', 'manager', 'cashier', 'storekeeper')
    permission_classes = [RolePermission]

    queryset = PaymentNotification.objects.all().order_by('-created_at')
    serializer_class = PaymentNotificationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message', 'channel']
    ordering_fields = ['created_at', 'is_read']

    def get_queryset(self):
        queryset = super().get_queryset()
        is_read = self.request.query_params.get('is_read')
        channel = self.request.query_params.get('channel')
        severity = self.request.query_params.get('severity')

        if is_read in ['true', 'false']:
            queryset = queryset.filter(is_read=is_read == 'true')

        if channel:
            queryset = queryset.filter(channel=channel)

        if severity:
            queryset = queryset.filter(severity=severity)

        return queryset

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return Response({'success': True})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({'success': True, 'updated': updated})

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        return Response({
            'unread_count': self.get_queryset().filter(is_read=False).count()
        })


class CashDrawerViewSet(viewsets.ModelViewSet):
    allowed_roles = ('admin', 'manager', 'cashier')
    permission_classes = [RolePermission]

    queryset = CashDrawer.objects.filter(is_active=True).order_by('-opened_at')
    serializer_class = CashDrawerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'cashier__username']
    ordering_fields = ['opened_at', 'status', 'expected_balance']

    def perform_create(self, serializer):
        drawer = serializer.save()
        if drawer.opening_balance and not drawer.expected_balance:
            drawer.expected_balance = drawer.opening_balance
            drawer.save(update_fields=['expected_balance'])
        CashDrawerTransaction.objects.create(
            drawer=drawer,
            transaction_type='opening',
            amount=drawer.opening_balance,
            note='Drawer opened',
        )

    @action(detail=True, methods=['post'], url_path='close')
    def close_drawer(self, request, pk=None):
        drawer = self.get_object()
        closing_balance = Decimal(str(request.data.get('closing_balance', drawer.expected_balance)))
        drawer.closing_balance = closing_balance
        drawer.status = 'closed'
        drawer.closed_at = timezone.now()
        drawer.save(update_fields=['closing_balance', 'status', 'closed_at'])

        CashDrawerTransaction.objects.create(
            drawer=drawer,
            transaction_type='closing',
            amount=closing_balance,
            note=request.data.get('note', 'Drawer closed'),
        )
        PaymentNotification.objects.create(
            channel='drawer',
            title='Cash drawer closed',
            message=f'{drawer.name} closed with KES {closing_balance}. Expected KES {drawer.expected_balance}.',
        )
        return Response({'success': True, 'drawer': CashDrawerSerializer(drawer).data})

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class CashDrawerTransactionViewSet(viewsets.ModelViewSet):
    allowed_roles = ('admin', 'manager', 'cashier')
    permission_classes = [RolePermission]

    queryset = CashDrawerTransaction.objects.all().order_by('-created_at')
    serializer_class = CashDrawerTransactionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['drawer__name', 'note', 'transaction_type']
    ordering_fields = ['created_at', 'amount', 'transaction_type']


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    body = request.data
    stk_callback = body.get('Body', {}).get('stkCallback', {})
    checkout_request_id = stk_callback.get('CheckoutRequestID', '')
    result_code = str(stk_callback.get('ResultCode', ''))
    result_description = stk_callback.get('ResultDesc', '')

    transaction = MpesaTransaction.objects.filter(checkout_request_id=checkout_request_id).first()
    if not transaction:
        transaction = MpesaTransaction.objects.create(
            phone_number='unknown',
            amount=0,
            checkout_request_id=checkout_request_id or None,
            status='failed',
            raw_callback=body,
            result_code=result_code,
            result_description=result_description or 'Unknown M-Pesa callback',
        )
        return Response({'ResultCode': 0, 'ResultDesc': 'Callback received'})

    if result_code == '0':
        metadata_items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        metadata = {item.get('Name'): item.get('Value') for item in metadata_items if item.get('Name')}
    else:
        metadata = {}

    confirm_mpesa_transaction(
        transaction=transaction,
        result_code=result_code,
        result_description=result_description,
        metadata=metadata,
        raw_callback=body,
    )
    return Response({'ResultCode': 0, 'ResultDesc': 'Callback received'})


@api_view(['GET'])
@permission_classes([AllowAny])
def mpesa_callback_config(request):
    local_callback = request.build_absolute_uri(reverse('mpesa_callback'))
    configured_callback = settings.MPESA_CALLBACK_URL
    is_public = configured_callback.startswith('https://') and 'localhost' not in configured_callback and '127.0.0.1' not in configured_callback

    return Response({
        'environment': settings.MPESA_ENVIRONMENT,
        'demo_mode': settings.MPESA_DEMO_MODE,
        'configured_callback_url': configured_callback,
        'local_callback_url': local_callback,
        'is_public_https_callback': is_public,
        'message': 'Use a public HTTPS callback URL for real Daraja confirmations.' if not is_public else 'Callback URL is suitable for Daraja.',
    })
