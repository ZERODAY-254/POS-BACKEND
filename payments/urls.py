from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    CashDrawerTransactionViewSet,
    CashDrawerViewSet,
    MpesaTransactionViewSet,
    PaymentNotificationViewSet,
    PaymentViewSet,
    mpesa_callback_config,
    mpesa_callback,
    mpesa_health,
)


router = DefaultRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'mpesa-transactions', MpesaTransactionViewSet)
router.register(r'payment-notifications', PaymentNotificationViewSet)
router.register(r'cash-drawers', CashDrawerViewSet)
router.register(r'cash-drawer-transactions', CashDrawerTransactionViewSet)

urlpatterns = [
    path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),
    path('mpesa/callback-config/', mpesa_callback_config, name='mpesa_callback_config'),
    path('mpesa/health/', mpesa_health, name='mpesa_health'),
    path('', include(router.urls)),
]
