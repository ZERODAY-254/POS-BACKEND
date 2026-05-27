from payments.models import (
    NotificationChannel as BaseNotificationChannel,
    NotificationLog as BaseNotificationLog,
    NotificationRule as BaseNotificationRule,
    NotificationTemplate as BaseNotificationTemplate,
    PaymentNotification as BasePaymentNotification,
)


class Notification(BasePaymentNotification):
    class Meta:
        proxy = True
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'


class NotificationChannel(BaseNotificationChannel):
    class Meta:
        proxy = True
        verbose_name = 'Notification channel'
        verbose_name_plural = 'Notification channels'


class NotificationTemplate(BaseNotificationTemplate):
    class Meta:
        proxy = True
        verbose_name = 'Notification template'
        verbose_name_plural = 'Notification templates'


class NotificationRule(BaseNotificationRule):
    class Meta:
        proxy = True
        verbose_name = 'Notification rule'
        verbose_name_plural = 'Notification rules'


class NotificationLog(BaseNotificationLog):
    class Meta:
        proxy = True
        verbose_name = 'Notification log'
        verbose_name_plural = 'Notification logs'
