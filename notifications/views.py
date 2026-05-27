from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import RolePermission
from payments.serializers import PaymentNotificationSerializer
from payments.views import PaymentNotificationViewSet
from payments.models import PaymentNotification

from .bot import NotificationBot


class NotificationViewSet(PaymentNotificationViewSet):
    pass


@api_view(['POST'])
@permission_classes([RolePermission])
def run_notification_bot(request):
    result = NotificationBot().run()
    return Response({'success': True, 'bot': NotificationBot.name, 'created': result})


@api_view(['GET'])
@permission_classes([RolePermission])
def notification_bot_status(request):
    return Response({
        'success': True,
        'bot': NotificationBot.name,
        'unread_count': PaymentNotification.objects.filter(is_read=False).count(),
        'latest': PaymentNotificationSerializer(
            PaymentNotification.objects.order_by('-created_at')[:10],
            many=True,
        ).data,
    })
