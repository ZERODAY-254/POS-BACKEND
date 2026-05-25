from rest_framework import serializers
from .models import CashDrawer, CashDrawerTransaction, MpesaTransaction, Payment, PaymentNotification


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'


class MpesaTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = MpesaTransaction
        fields = '__all__'


class PaymentNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentNotification
        fields = '__all__'


class CashDrawerSerializer(serializers.ModelSerializer):

    class Meta:
        model = CashDrawer
        fields = '__all__'


class CashDrawerTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CashDrawerTransaction
        fields = '__all__'
