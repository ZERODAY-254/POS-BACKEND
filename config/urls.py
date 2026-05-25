from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/accounts/', include('accounts.urls')),

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
