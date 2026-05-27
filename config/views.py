from django.conf import settings
from django.db import connection
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    database_ok = True
    database_error = ''

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as exc:
        database_ok = False
        database_error = str(exc)

    data = {
        'status': 'ok' if database_ok else 'error',
        'database': {
            'ok': database_ok,
            'engine': settings.DATABASES['default']['ENGINE'],
            'name': settings.DATABASES['default']['NAME'],
        },
        'debug': settings.DEBUG,
        'auth_header': 'Authorization: Bearer <access_token>',
    }

    if database_error:
        data['database']['error'] = database_error

    return Response(data, status=200 if database_ok else 503)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_endpoints(request):
    return Response({
        'health': request.build_absolute_uri(reverse('api_health')),
        'auth': {
            'login': request.build_absolute_uri('/api/auth/login/'),
            'refresh': request.build_absolute_uri('/api/auth/token/refresh/'),
            'me': request.build_absolute_uri('/api/auth/me/'),
            'register': request.build_absolute_uri('/api/auth/register/'),
        },
        'core': {
            'products': request.build_absolute_uri('/api/products/'),
            'categories': request.build_absolute_uri('/api/products/categories/'),
            'stock_alerts': request.build_absolute_uri('/api/products/stock-alerts/'),
            'sales': request.build_absolute_uri('/api/sales/'),
            'payments': request.build_absolute_uri('/api/payments/'),
            'mpesa_health': request.build_absolute_uri('/api/mpesa/health/'),
            'mpesa_callback': request.build_absolute_uri('/api/mpesa/callback/'),
            'reports_summary': request.build_absolute_uri('/api/reports/summary/'),
            'dashboard_charts': request.build_absolute_uri('/api/dashboard/charts/'),
            'excel_products_template': request.build_absolute_uri('/api/excel/template/products/'),
            'automatic_excel_status': request.build_absolute_uri('/api/excel/automatic/'),
            'automatic_excel_rebuild': request.build_absolute_uri('/api/excel/automatic/rebuild/'),
        },
        'note': 'Protected endpoints require Authorization: Bearer <access_token>.',
    })
