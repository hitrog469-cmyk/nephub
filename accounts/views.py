from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.conf import settings
from .forms import SignUpForm, ProfileForm, UsernameForm
from .models import UserProfile, EmailVerification
from .throttle import rate_limit


# ── helpers ───────────────────────────────────────────────────────────────────

def _send_code_email(user, code):
    """Email the 6-digit verification code. Returns True if it sent."""
    subject = 'Your NepHub verification code'
    text_body = (
        f"Hi {user.username},\n\n"
        f"Your NepHub verification code is: {code}\n\n"
        f"Enter it on the verification page to activate your account.\n"
        f"This code expires in {EmailVerification.CODE_TTL_MINUTES} minutes.\n\n"
        f"If you didn't sign up for NepHub, you can ignore this email.\n\n"
        f"— The NepHub Team"
    )
    html_body = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:32px 24px;background:#f8fafc;border-radius:12px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#1d4ed8;font-size:1.6rem;margin:0;">NepHub</h1>
        <p style="color:#64748b;font-size:.85rem;margin-top:4px;">Jobs, Loksewa &amp; scholarships in Nepal</p>
      </div>
      <div style="background:#fff;border-radius:10px;padding:28px 24px;border:1px solid #e2e8f0;">
        <h2 style="margin:0 0 12px;font-size:1.15rem;color:#1e293b;">Verify your email address</h2>
        <p style="color:#475569;font-size:.9rem;line-height:1.6;margin:0 0 20px;">
          Hi <strong>{user.username}</strong>, enter this code to activate your account:
        </p>
        <div style="text-align:center;margin:24px 0;">
          <div style="display:inline-block;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                      padding:16px 32px;font-size:2rem;font-weight:800;letter-spacing:.4em;color:#1d4ed8;">
            {code}
          </div>
        </div>
        <p style="color:#94a3b8;font-size:.78rem;text-align:center;margin:16px 0 0;">
          This code expires in {EmailVerification.CODE_TTL_MINUTES} minutes. If you didn't sign up for NepHub, ignore this email.
        </p>
      </div>
      <p style="color:#cbd5e1;font-size:.73rem;text-align:center;margin-top:20px;">
        © NepHub · Jobs &amp; opportunities in Nepal
      </p>
    </div>
    """
    msg = EmailMultiAlternatives(subject, text_body,
                                 settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_body, 'text/html')
    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        return False


# ── signup ────────────────────────────────────────────────────────────────────

@rate_limit('signup', max_attempts=6, window_seconds=600)
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Clear out any abandoned, unverified signup using this email.
            from django.contrib.auth import get_user_model
            get_user_model().objects.filter(email__iexact=email, is_active=False).delete()

            user = form.save(commit=False)
            user.is_active = False          # blocked until email verified
            user.save()
            UserProfile.objects.get_or_create(user=user)

            ev, _ = EmailVerification.objects.get_or_create(user=user)
            ev.refresh_code()
            sent = _send_code_email(user, ev.code)

            request.session['pending_verification_user'] = user.pk
            if not sent:
                messages.error(
                    request,
                    "We couldn't send your code right now. Tap 'Resend code' to try again."
                )
            return redirect('verify_code')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def _pending_user(request):
    from django.contrib.auth import get_user_model
    pk = request.session.get('pending_verification_user')
    if not pk:
        return None
    return get_user_model().objects.filter(pk=pk, is_active=False).first()


def verify_code_view(request):
    """Enter the 6-digit code emailed at signup. Activates + logs in on success."""
    user = _pending_user(request)
    if user is None:
        return redirect('signup')

    ev = EmailVerification.objects.filter(user=user).first()

    if request.method == 'POST':
        entered = request.POST.get('code', '').strip()
        if ev is None:
            messages.error(request, 'Something went wrong. Please sign up again.')
            return redirect('signup')
        if ev.is_expired:
            messages.error(request, 'That code has expired. Tap "Resend code" for a new one.')
        elif ev.too_many_attempts:
            messages.error(request, 'Too many attempts. Tap "Resend code" to start over.')
        elif entered == ev.code:
            user.is_active = True
            user.save(update_fields=['is_active'])
            ev.delete()
            request.session.pop('pending_verification_user', None)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Email verified — welcome to NepHub!')
            return redirect('post_login')
        else:
            ev.attempts += 1
            ev.save(update_fields=['attempts'])
            messages.error(request, 'Incorrect code. Please check and try again.')

    return render(request, 'accounts/verify_code.html', {'email': _mask_email(user.email)})


def _mask_email(email):
    try:
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            shown = local[0] + '*'
        else:
            shown = local[0] + '*' * (len(local) - 2) + local[-1]
        return f"{shown}@{domain}"
    except ValueError:
        return email


@rate_limit('resend_code', max_attempts=4, window_seconds=600)
def resend_code_view(request):
    user = _pending_user(request)
    if user is None:
        return redirect('signup')
    ev, _ = EmailVerification.objects.get_or_create(user=user)
    ev.refresh_code()
    if _send_code_email(user, ev.code):
        messages.success(request, 'A new code is on its way to your inbox.')
    else:
        messages.error(request, "We couldn't send the code. Please try again in a moment.")
    return redirect('verify_code')


# ── login ─────────────────────────────────────────────────────────────────────

@rate_limit('login', max_attempts=10, window_seconds=300)
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
    New Google users → choose username first.
    New users (0% profile) → profile page with welcome banner.
    Returning users → homepage.
    """
    # New Google/social signup — ask them to pick a username
    if request.session.pop('needs_username', False):
        return redirect('choose_username')

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


@login_required
def choose_username_view(request):
    """Let new Google OAuth users pick their own username."""
    if request.method == 'POST':
        form = UsernameForm(request.POST)
        if form.is_valid():
            request.user.username = form.cleaned_data['username']
            request.user.save(update_fields=['username'])
            messages.success(
                request,
                f'Welcome to NepHub, {request.user.username}! '
                'Your account is ready — fill in your profile to unlock more features.'
            )
            return redirect('profile')
    else:
        form = UsernameForm()
    return render(request, 'accounts/choose_username.html', {'form': form})


# ── username availability check (AJAX) ───────────────────────────────────────

def check_username_view(request):
    username = request.GET.get('u', '').strip()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    taken = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': not taken})


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
