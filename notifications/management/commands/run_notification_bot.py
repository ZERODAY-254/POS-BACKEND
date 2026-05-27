from django.core.management.base import BaseCommand

from notifications.bot import NotificationBot


class Command(BaseCommand):
    help = 'Run the POS notification bot checks.'

    def handle(self, *args, **options):
        result = NotificationBot().run()
        self.stdout.write(self.style.SUCCESS(f'Notification bot completed: {result}'))
