import os

from django.db import migrations


def set_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN') or os.environ.get('SITE_DOMAIN', '')
    if not domain:
        # fall back to first ALLOWED_HOSTS entry that isn't localhost
        raw = os.environ.get('ALLOWED_HOSTS', '')
        hosts = [h.strip() for h in raw.split(',') if h.strip() and 'localhost' not in h and '127.0.0.1' not in h]
        domain = hosts[0] if hosts else '127.0.0.1:8000'
    Site.objects.update_or_create(
        pk=1, defaults={'domain': domain, 'name': 'NepHub'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_alter_job_deadline'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, migrations.RunPython.noop),
    ]
