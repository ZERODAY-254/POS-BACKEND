from django.db import migrations


DEFAULT_CATEGORIES = (
    ('Laptops', 'Portable computers and notebooks.'),
    ('Desktops', 'Desktop computers, towers, and all-in-one PCs.'),
    ('Monitors', 'Computer screens and display accessories.'),
    ('Printers & Scanners', 'Printers, scanners, toner, ink, and related devices.'),
    ('Networking', 'Routers, switches, cables, access points, and network tools.'),
    ('Keyboards & Mice', 'Keyboards, mice, touchpads, and input accessories.'),
    ('Storage Devices', 'Hard drives, SSDs, flash disks, memory cards, and storage accessories.'),
    ('Computer Accessories', 'Chargers, adapters, bags, stands, and general accessories.'),
    ('Software', 'Licenses, operating systems, antivirus, and business software.'),
    ('POS Hardware', 'Barcode scanners, receipt printers, cash drawers, and POS terminals.'),
    ('Spare Parts', 'RAM, batteries, screens, motherboards, fans, and replacement parts.'),
    ('Services', 'Repairs, maintenance, installation, and technical support.'),
)


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    for name, description in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            name=name,
            defaults={'description': description, 'is_active': True},
        )


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(name__in=[name for name, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_alter_batch_options_alter_category_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, remove_default_categories),
    ]
