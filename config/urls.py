from django.contrib import admin
from django.urls import path, include
from products.views import product_detail, product_list
from .views import api_endpoints, health_check

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/health/', health_check, name='api_health'),
    path('api/endpoints/', api_endpoints, name='api_endpoints'),

    path('api/products', product_list),
    path('api/products/<int:product_id>', product_detail),

    path('api/auth/', include('accounts.urls')),
    path('api/accounts/', include('accounts.urls')),

    path('api/notifications/', include('notifications.urls')),

    path('api/mpesa-app/', include('mpesa.urls')),

    path('api/reports-app/', include('reports.urls')),

    path('api/inventory-app/', include('inventory.urls')),

    path('api/', include('api.urls')),

    path('api/', include('products.urls')),

    path('api/', include('salesapp.urls')),

    path('api/', include('customers.urls')),

    path('api/', include('payments.urls')),

    path('api/', include('returns.urls')),

    path('api/', include('orders.urls')),

    path('api/', include('audit.urls')),

    path('api/products/', include('products.urls')),
]
