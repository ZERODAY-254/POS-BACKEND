from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer
from audit.models import AuditLog
from salesapp.models import Sale


class CustomerViewSet(viewsets.ModelViewSet):

    queryset = Customer.objects.filter(is_active=True).order_by('name')

    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone', 'account_reference']
    ordering_fields = ['name', 'email']

    def perform_create(self, serializer):
        customer = serializer.save()
        AuditLog.objects.create(action='Created customer', module='Customers', actor='frontend', details=customer.name)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        AuditLog.objects.create(action='Deactivated customer', module='Customers', actor='frontend', details=instance.name)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        query = request.query_params.get('q') or request.query_params.get('search') or ''
        queryset = self.filter_queryset(self.get_queryset())
        if query:
            queryset = queryset.filter(name__icontains=query) | queryset.filter(phone__icontains=query) | queryset.filter(email__icontains=query)
        return Response(CustomerSerializer(queryset.order_by('name')[:50], many=True).data)

    @action(detail=True, methods=['post'], url_path='add_loyalty_points')
    def add_loyalty_points(self, request, pk=None):
        customer = self.get_object()
        return Response({
            'success': True,
            'message': 'Loyalty points endpoint is ready. Add loyalty fields to Customer model when needed.',
            'customer': CustomerSerializer(customer).data,
        })

    @action(detail=True, methods=['post'], url_path='update_credit')
    def update_credit(self, request, pk=None):
        customer = self.get_object()
        return Response({
            'success': True,
            'message': 'Credit endpoint is ready. Add credit fields to Customer model when needed.',
            'customer': CustomerSerializer(customer).data,
        })

    @action(detail=True, methods=['get'], url_path='purchase_history')
    def purchase_history(self, request, pk=None):
        customer = self.get_object()
        sales = Sale.objects.filter(customer_name__iexact=customer.name, is_active=True).order_by('-created_at')[:100]
        return Response([
            {
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'invoice_number': sale.invoice_number,
                'grand_total': sale.grand_total,
                'payment_method': sale.payment_method,
                'payment_status': sale.payment_status,
                'created_at': sale.created_at,
            }
            for sale in sales
        ], status=status.HTTP_200_OK)
