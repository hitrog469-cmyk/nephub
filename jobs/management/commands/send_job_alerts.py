"""
Management command: send_job_alerts

Sends email digests to all verified JobAlert subscribers whose subscribed
categories overlap with jobs posted in the last N hours (default 24).

Usage:
    python manage.py send_job_alerts
    python manage.py send_job_alerts --hours 48
"""
import datetime
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from jobs.models import Job, JobAlert


class Command(BaseCommand):
    help = 'Send job alert digests to verified subscribers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Look back this many hours for new jobs (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print emails to stdout without sending',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        since = timezone.now() - datetime.timedelta(hours=hours)

        alerts = JobAlert.objects.filter(is_active=True, is_verified=True).prefetch_related('tags')
        sent = skipped = 0

        for alert in alerts:
            jobs = self._matching_jobs(alert, since)
            if not jobs:
                skipped += 1
                continue

            body = self._build_body(alert, jobs)

            if dry_run:
                self.stdout.write(f'\n--- DRY RUN: to {alert.email} ---\n{body}\n')
            else:
                send_mail(
                    subject=f'[NepHub] {len(jobs)} new job{"s" if len(jobs) != 1 else ""} for you',
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[alert.email],
                    fail_silently=False,
                )
            sent += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Sent: {sent}  Skipped (no matches): {skipped}'
        ))

    def _matching_jobs(self, alert, since):
        today = timezone.now().date()
        qs = Job.objects.filter(
            is_active=True,
            deadline__gte=today,
            date_posted__gte=since,
        ).prefetch_related('tags')

        if alert.subscribed_categories:
            qs = qs.filter(category__in=alert.subscribed_categories)

        alert_tag_ids = set(alert.tags.values_list('id', flat=True))
        if alert_tag_ids:
            qs = qs.filter(tags__id__in=alert_tag_ids).distinct()

        return list(qs[:20])

    def _build_body(self, alert, jobs):
        lines = [
            'Hi,\n',
            f'Here are {len(jobs)} new job{"s" if len(jobs) != 1 else ""} matching your NepHub alert:\n',
        ]
        for job in jobs:
            deadline = job.deadline.strftime('%b %d, %Y')
            lines.append(f'• {job.title} — {job.organization}')
            lines.append(f'  Deadline: {deadline}')
            if job.apply_link:
                lines.append(f'  Apply: {job.apply_link}')
            lines.append('')

        lines += [
            '---',
            'Browse all jobs at https://nephub.com/',
            'To unsubscribe, reply to this email or visit your profile settings.',
            '',
            '— NepHub Team',
        ]
        return '\n'.join(lines)
