from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .forms import SignUpForm, ProfileForm
from .models import UserProfile


# ── helpers ───────────────────────────────────────────────────────────────────

def _send_verification_email(request, user):
    token = signing.dumps(user.pk, salt='nephub-email-verify')
    link  = request.build_absolute_uri(f'/accounts/verify-email/{token}/')
    subject = 'Verify your NepHub account'
    text_body = (
        f"Hi {user.username},\n\n"
        f"Thanks for joining NepHub! Click the link below to verify your email:\n\n"
        f"{link}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"— The NepHub Team"
    )
    html_body = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:32px 24px;background:#f8fafc;border-radius:12px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#1d4ed8;font-size:1.6rem;margin:0;">NepHub</h1>
        <p style="color:#64748b;font-size:.85rem;margin-top:4px;">Nepal's trusted job portal</p>
      </div>
      <div style="background:#fff;border-radius:10px;padding:28px 24px;border:1px solid #e2e8f0;">
        <h2 style="margin:0 0 12px;font-size:1.15rem;color:#1e293b;">Verify your email address</h2>
        <p style="color:#475569;font-size:.9rem;line-height:1.6;margin:0 0 20px;">
          Hi <strong>{user.username}</strong>,<br>
          Thanks for creating a NepHub account! Click the button below to verify your email and activate your account.
        </p>
        <div style="text-align:center;margin:24px 0;">
          <a href="{link}"
             style="background:#1d4ed8;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:.95rem;display:inline-block;">
            Verify My Email →
          </a>
        </div>
        <p style="color:#94a3b8;font-size:.78rem;text-align:center;margin:16px 0 0;">
          This link expires in 24 hours. If you didn't sign up for NepHub, you can ignore this email.
        </p>
      </div>
      <p style="color:#cbd5e1;font-size:.73rem;text-align:center;margin-top:20px;">
        © NepHub · Nepal's Job Portal
      </p>
    </div>
    """
    msg = EmailMultiAlternatives(subject, text_body,
                                 settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=True)


# ── signup ────────────────────────────────────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False          # blocked until email verified
            user.save()
            UserProfile.objects.get_or_create(user=user)
            _send_verification_email(request, user)
            return redirect('verification_sent')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def verification_sent_view(request):
    return render(request, 'accounts/verification_sent.html')


def verify_email_view(request, token):
    try:
        user_pk = signing.loads(token, salt='nephub-email-verify', max_age=86400)
    except signing.SignatureExpired:
        return render(request, 'accounts/verify_result.html', {
            'success': False,
            'message': 'This verification link has expired. Please sign up again.',
        })
    except signing.BadSignature:
        return render(request, 'accounts/verify_result.html', {
            'success': False,
            'message': 'Invalid verification link.',
        })

    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return render(request, 'accounts/verify_result.html', {
            'success': False, 'message': 'Account not found.',
        })

    user.is_active = True
    user.save(update_fields=['is_active'])
    return render(request, 'accounts/verify_result.html', {
        'success': True,
        'username': user.username,
    })


# ── login ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = ''
            if next_url:
                return redirect(next_url)
            return redirect('post_login')     # handled centrally
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


# ── post-login redirect (covers email login + Google OAuth) ───────────────────

@login_required
def post_login_view(request):
    """
    Central landing after any login — email or Google OAuth.
    New users (0% profile) → profile page with welcome banner.
    Returning users → homepage.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.completion_pct == 0:
        messages.success(
            request,
            f'Welcome to NepHub, {request.user.username}! '
            'Your account is ready. Filling in your profile is optional — '
            'but it unlocks personalised job recommendations, CV storage and more.'
        )
        return redirect('profile')
    return redirect('/')


# ── logout ────────────────────────────────────────────────────────────────────

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')


# ── profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            p = form.save(commit=False)
            if 'cv' in request.FILES:
                p.cv_uploaded_at = timezone.now()
            p.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    from jobs.models import SavedJob, Job, JobAlert
    from django.db.models import Q
    saved_jobs_qs = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    saved_count   = saved_jobs_qs.count()
    recent_saved  = saved_jobs_qs[:4]
    today         = timezone.now().date()

    recommended = (
        Job.objects
        .filter(is_active=True)
        .filter(Q(deadline__gte=today) | Q(deadline__isnull=True))
        .order_by('-is_featured', '-date_posted')[:6]
    )

    urgent_saved = [
        s for s in saved_jobs_qs
        if s.job.deadline and 0 <= (s.job.deadline - today).days <= 7
    ]
    alert = JobAlert.objects.filter(email=request.user.email).first()

    return render(request, 'accounts/profile.html', {
        'form':         form,
        'profile':      profile,
        'saved_count':  saved_count,
        'recent_saved': recent_saved,
        'recommended':  recommended,
        'urgent_saved': urgent_saved,
        'alert':        alert,
        'today':        today,
    })
