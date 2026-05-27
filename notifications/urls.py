from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, notification_bot_status, run_notification_bot


router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification-app')

urlpatterns = [
    path('bot/run/', run_notification_bot, name='notification_bot_run'),
    path('bot/status/', notification_bot_status, name='notification_bot_status'),
    path('', include(router.urls)),
]
