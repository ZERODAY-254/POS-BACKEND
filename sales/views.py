from django.shortcuts import render
from rest_framework import viewsets
from products.models import Product
from customers.models import Customer
from sales.models import Sale
from .serializers import SaleSerializer


class SaleViewSet(viewsets.ModelViewSet):

    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

def dashboard(request):
    total_products = Product.objects.count()
    total_customers = Customer.objects.count()
    total_sales = Sale.objects.count()

    context = {
        'total_products': total_products,
        'total_customers': total_customers,
        'total_sales': total_sales,
    }

    return render(request, 'dashboard.html', context)
