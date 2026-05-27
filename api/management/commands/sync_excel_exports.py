from django.core.management.base import BaseCommand

from api.excel_sync import EXPORTS, sync_all_excel_exports, sync_excel_export


class Command(BaseCommand):
    help = 'Rebuild automatic Excel export files from current database data.'

    def add_arguments(self, parser):
        parser.add_argument(
            'export_name',
            nargs='?',
            choices=sorted(EXPORTS.keys()),
            help='Optional single export to rebuild.',
        )

    def handle(self, *args, **options):
        export_name = options.get('export_name')
        if export_name:
            path = sync_excel_export(export_name)
            self.stdout.write(self.style.SUCCESS(f'Rebuilt {export_name}: {path}'))
            return

        for name, path in sync_all_excel_exports().items():
            self.stdout.write(self.style.SUCCESS(f'Rebuilt {name}: {path}'))
