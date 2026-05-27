from django.core.management.base import BaseCommand

from payments.models import PaymentNotification


class Command(BaseCommand):
    help = 'Create demo notifications for manual testing.'

    def handle(self, *args, **options):
        samples = [
            {
                'channel': 'inventory',
                'severity': 'warning',
                'title': 'Demo low stock alert',
                'message': 'Demo Product stock is below the minimum level.',
                'action_url': '/inventory',
            },
            {
                'channel': 'mpesa',
                'severity': 'success',
                'title': 'Demo M-Pesa payment received',
                'message': 'Demo M-Pesa receipt confirmed successfully.',
                'action_url': '/payments',
            },
            {
                'channel': 'reports',
                'severity': 'info',
                'title': 'Demo daily report ready',
                'message': 'Today sales summary is ready for review.',
                'action_url': '/reports',
            },
            {
                'channel': 'system',
                'severity': 'error',
                'title': 'Demo system warning',
                'message': 'This is a demo error notification for testing.',
                'action_url': '/dashboard',
            },
        ]

        created = 0
        for sample in samples:
            _, was_created = PaymentNotification.objects.get_or_create(
                title=sample['title'],
                defaults=sample,
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f'Demo notifications ready. Created {created} new notifications.'))
