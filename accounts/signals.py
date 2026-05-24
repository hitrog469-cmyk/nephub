from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(social_account_added)
def flag_new_social_user(sender, request, sociallogin, **kwargs):
    """Mark new Google/social signups so we can ask them to choose a username."""
    request.session['needs_username'] = True
