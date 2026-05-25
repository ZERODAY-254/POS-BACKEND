from rest_framework import filters, viewsets
from .models import Return
from .serializers import ReturnSerializer


class ReturnViewSet(viewsets.ModelViewSet):

    queryset = Return.objects.filter(is_active=True).order_by('-returned_at')
    serializer_class = ReturnSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'item_name', 'reason', 'status']
    ordering_fields = ['returned_at', 'amount', 'status']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
