"""
Wipe all non-admin user data for a clean launch.

Deletes every user that is NOT a superuser (and their profiles, saved jobs
via cascade), and clears job-alert subscribers and advertise inquiries.
Superuser/admin accounts are always preserved.

Usage:
    python manage.py reset_users          # asks for confirmation
    python manage.py reset_users --yes     # no prompt (for scripts)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Delete all non-superuser accounts and clear subscribers/inquiries.'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true',
                            help='Skip the confirmation prompt.')

    def handle(self, *args, **options):
        from jobs.models import JobAlert, AdInquiry

        non_admin = User.objects.filter(is_superuser=False)
        user_count = non_admin.count()
        admin_count = User.objects.filter(is_superuser=True).count()
        alert_count = JobAlert.objects.count()
        inquiry_count = AdInquiry.objects.count()

        self.stdout.write(self.style.WARNING(
            f'\nThis will permanently delete:\n'
            f'  - {user_count} user account(s) (+ their profiles & saved jobs)\n'
            f'  - {alert_count} job-alert subscriber(s)\n'
            f'  - {inquiry_count} advertise inquiry(ies)\n'
            f'And KEEP {admin_count} superuser/admin account(s).\n'
        ))

        if not options['yes']:
            confirm = input("Type 'DELETE' to proceed: ").strip()
            if confirm != 'DELETE':
                self.stdout.write(self.style.ERROR('Aborted. Nothing was deleted.'))
                return

        deleted_users, _ = non_admin.delete()
        JobAlert.objects.all().delete()
        AdInquiry.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'Done. Removed {user_count} user(s), {alert_count} subscriber(s), '
            f'{inquiry_count} inquiry(ies). Admin accounts preserved.'
        ))
