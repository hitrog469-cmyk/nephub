import datetime
import secrets

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EmailVerification(models.Model):
    """A short-lived 6-digit code used to verify a new account's email
    before the account can log in."""

    CODE_TTL_MINUTES = 15
    MAX_ATTEMPTS = 6

    user      = models.OneToOneField(User, on_delete=models.CASCADE,
                                     related_name='email_verification')
    code      = models.CharField(max_length=6)
    sent_at   = models.DateTimeField(default=timezone.now)
    attempts  = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Verification for {self.user.username}"

    @staticmethod
    def new_code():
        return f"{secrets.randbelow(1_000_000):06d}"

    def refresh_code(self):
        """Issue a fresh code and reset the clock + attempt counter."""
        self.code = self.new_code()
        self.sent_at = timezone.now()
        self.attempts = 0
        self.save(update_fields=['code', 'sent_at', 'attempts'])

    @property
    def is_expired(self):
        return timezone.now() > self.sent_at + datetime.timedelta(minutes=self.CODE_TTL_MINUTES)

    @property
    def too_many_attempts(self):
        return self.attempts >= self.MAX_ATTEMPTS


class UserProfile(models.Model):

    EXPERIENCE_CHOICES = [
        ('',        'Not specified'),
        ('student', 'Student'),
        ('entry',   'Entry Level (0–2 yrs)'),
        ('mid',     'Mid Level (2–5 yrs)'),
        ('senior',  'Senior Level (5+ yrs)'),
    ]

    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # ── Personal info ──────────────────────────────────────────────
    full_name      = models.CharField(max_length=120, blank=True,
                                      help_text='Your real name (shown on profile)')
    phone          = models.CharField(max_length=20, blank=True)
    location       = models.CharField(max_length=80, blank=True,
                                      help_text='e.g. Kathmandu, Bagmati Province')
    experience     = models.CharField(max_length=20, blank=True,
                                      choices=EXPERIENCE_CHOICES,
                                      help_text='Helps us recommend the right jobs')
    bio            = models.TextField(blank=True, max_length=600,
                                      help_text='Brief intro — skills, interests, goals')
    linkedin_url   = models.URLField(blank=True,
                                     help_text='linkedin.com/in/yourprofile')
    website_url    = models.URLField(blank=True,
                                     help_text='Portfolio, GitHub or personal website')

    # ── CV ─────────────────────────────────────────────────────────
    cv             = models.FileField(upload_to='cvs/', blank=True, null=True)
    cv_uploaded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def has_cv(self):
        return bool(self.cv)

    @property
    def display_name(self):
        """Full name if set, otherwise username."""
        return self.full_name.strip() or self.user.username

    @property
    def completion_pct(self):
        """Profile completeness 0–100."""
        fields = [
            bool(self.full_name),
            bool(self.phone),
            bool(self.location),
            bool(self.experience),
            bool(self.bio),
            bool(self.cv),
            bool(self.linkedin_url),
        ]
        done = sum(fields)
        return int((done / len(fields)) * 100)
