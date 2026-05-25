from rest_framework import filters, viewsets

from .models import Customer
from .serializers import CustomerSerializer
from audit.models import AuditLog


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
