from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MpesaViewSet, mpesa_callback, mpesa_callback_config, mpesa_health


router = DefaultRouter()
router.register(r'transactions', MpesaViewSet, basename='mpesa-app-transaction')

urlpatterns = [
    path('callback/', mpesa_callback, name='mpesa_app_callback'),
    path('callback-config/', mpesa_callback_config, name='mpesa_app_callback_config'),
    path('health/', mpesa_health, name='mpesa_app_health'),
    path('', include(router.urls)),
]
