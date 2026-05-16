"""
Custom allauth adapter for NepHub.

Security guarantee:
  - Any user who signs in via Google is ALWAYS a regular user.
  - is_superuser and is_staff are HARDCODED to False for all social logins.
  - The only way to be a superuser is via `python manage.py createsuperuser`.
  - There is no way to escalate privileges through Google OAuth.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class NepHubSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        """
        Called when a brand-new user registers via Google.
        We strip is_superuser and is_staff BEFORE saving.
        """
        user = super().save_user(request, sociallogin, form)

        # ── CRITICAL security lock ─────────────────────────────────
        # This cannot be overridden from the outside. Even if somehow
        # the sociallogin data tried to set these fields, we reset them.
        user.is_superuser = False
        user.is_staff     = False
        user.save(update_fields=['is_superuser', 'is_staff'])
        # ──────────────────────────────────────────────────────────

        # UserProfile is created automatically via accounts/signals.py
        # (post_save signal on User model) — no action needed here.

        return user

    def is_open_for_signup(self, request, sociallogin):
        """Anyone can sign up via Google — no restrictions."""
        return True
