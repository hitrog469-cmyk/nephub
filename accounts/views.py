from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import SignUpForm, ProfileForm
from .models import UserProfile


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to NepHub, {user.username}!')
            return redirect('/')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', '/')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = '/'
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')


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

    # ── Context: saved jobs ────────────────────────────────────────
    from jobs.models import SavedJob, Job
    saved_jobs_qs   = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    saved_count     = saved_jobs_qs.count()
    recent_saved    = saved_jobs_qs[:4]                 # show 4 on profile

    # ── Context: recommended jobs (simple — active, not expired) ──
    recommended = (
        Job.objects
        .filter(is_active=True, deadline__gte=timezone.now().date())
        .order_by('-is_featured', '-date_posted')[:6]
    )

    # ── Context: upcoming deadlines from saved jobs ────────────────
    today       = timezone.now().date()
    urgent_saved = [
        s for s in saved_jobs_qs
        if s.job.deadline and 0 <= (s.job.deadline - today).days <= 7
    ]

    # ── Context: email alert subscription ─────────────────────────
    from jobs.models import JobAlert
    alert = JobAlert.objects.filter(email=request.user.email).first()

    return render(request, 'accounts/profile.html', {
        'form':           form,
        'profile':        profile,
        'saved_count':    saved_count,
        'recent_saved':   recent_saved,
        'recommended':    recommended,
        'urgent_saved':   urgent_saved,
        'alert':          alert,
        'today':          today,
    })
