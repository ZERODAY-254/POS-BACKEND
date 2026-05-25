from rest_framework import filters, viewsets
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):

    queryset = Order.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = OrderSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['tracking_code', 'customer_name', 'product_name', 'phone', 'status']
    ordering_fields = ['created_at', 'total_amount', 'status', 'payment_status']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
