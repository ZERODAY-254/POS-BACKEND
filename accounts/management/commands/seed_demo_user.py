from django.core.management.base import BaseCommand

from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create or update a demo manager user for API testing.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='manager')
        parser.add_argument('--password', default='Manager@12345')
        parser.add_argument('--email', default='manager@example.com')
        parser.add_argument('--role', default='manager')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        role = options['role']

        allowed_roles = {choice[0] for choice in CustomUser.ROLE_CHOICES}
        if role not in allowed_roles:
            self.stderr.write(self.style.ERROR(f'Invalid role: {role}'))
            return

        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'role': role,
                'is_staff': role in {'admin', 'manager'},
                'is_superuser': role == 'admin',
            },
        )
        user.email = email
        user.role = role
        user.is_active = True
        user.is_staff = role in {'admin', 'manager'}
        user.is_superuser = role == 'admin'
        user.set_password(password)
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{action} API test user: username={username} password={password} role={role}'
        ))
