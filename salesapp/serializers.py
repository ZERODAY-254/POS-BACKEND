from rest_framework import serializers
from .models import Sale

class SaleSerializer(serializers.ModelSerializer):
    receipt_url = serializers.SerializerMethodField()
    print_receipt_url = serializers.SerializerMethodField()
    invoice_url = serializers.SerializerMethodField()
    print_invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = '__all__'

    def _sale_action_url(self, obj, action):
        path = f'/api/sales/{obj.pk}/{action}/'
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(path)
        return path

    def get_receipt_url(self, obj):
        return self._sale_action_url(obj, 'receipt')

    def get_print_receipt_url(self, obj):
        return self._sale_action_url(obj, 'print-receipt')

    def get_invoice_url(self, obj):
        return self._sale_action_url(obj, 'invoice')

    def get_print_invoice_url(self, obj):
        return self._sale_action_url(obj, 'print-invoice')
