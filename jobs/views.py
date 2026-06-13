import datetime
import logging
from functools import wraps

logger = logging.getLogger('jobs')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q, F, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import Job, SavedJob, Category, Tag, JobAlert, PROVINCE_CHOICES, JobType, ExperienceLevel
from .forms import JobAlertForm, JobFilterForm, AdminJobForm


# ── Superuser guard ────────────────────────────────────────────────
def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if not request.user.is_superuser:
            messages.error(request, 'Access denied.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper

CATEGORY_META = {
    'government': {
        'label': 'Government Jobs',
        'icon':  'building-2',
        'color': '#1e40af',
        'light': '#eff6ff',
        'desc':  'Official government vacancies from ministries, departments, and public bodies across Nepal.',
        'tips':  [
            'Check official ministry websites for primary sources',
            'Deadlines are strict — apply at least 3 days early',
            'Age limits and citizenship requirements apply',
        ],
    },
    'loksewa': {
        'label': 'Loksewa Vacancies',
        'icon':  'clipboard-list',
        'color': '#15803d',
        'light': '#f0fdf4',
        'desc':  'Public Service Commission (Lok Sewa Aayog) exam notifications and civil service vacancies.',
        'tips':  [
            'Register at psc.gov.np for official notifications',
            'Prepare using past 5 years question papers',
            'Physical fitness requirements apply for some posts',
        ],
    },
    'private': {
        'label': 'Private Sector Jobs',
        'icon':  'briefcase',
        'color': '#c2410c',
        'light': '#fff7ed',
        'desc':  "Career opportunities from Nepal's leading private companies, NGOs, INGOs, and startups.",
        'tips':  [
            'Tailor your CV for each application',
            'LinkedIn profile strengthens your application',
            'Follow up within one week of applying',
        ],
    },
    'scholarship': {
        'label': 'Scholarships',
        'icon':  'book-open',
        'color': '#a21caf',
        'light': '#fdf4ff',
        'desc':  'Fully-funded and partial scholarships for Nepali students — local and international programs.',
        'tips':  [
            'Prepare language test scores early (IELTS/TOEFL)',
            'Statement of Purpose matters most',
            'Apply to 5–10 programs to increase your chances',
        ],
    },
    'foreign': {
        'label': 'Foreign Employment',
        'icon':  'plane',
        'color': '#be123c',
        'light': '#fff1f2',
        'desc':  'DOFE-approved foreign employment opportunities in Qatar, UAE, Malaysia, Japan, and more.',
        'tips':  [
            'Only use DOFE-licensed manpower companies',
            'Verify the company at dofe.gov.np before paying any fee',
            'Know your rights as a migrant worker',
        ],
    },
    'internship': {
        'label': 'Internships',
        'icon':  'graduation-cap',
        'color': '#0369a1',
        'light': '#f0f9ff',
        'desc':  'Paid and unpaid internship programmes for students and fresh graduates across Nepal.',
        'tips':  [
            'Internships often convert to full-time roles — impress early',
            'Mention relevant coursework and projects in your CV',
            'Apply 2–3 months before your semester break',
        ],
    },
    'opportunity': {
        'label': 'Opportunities',
        'icon':  'star',
        'color': '#b45309',
        'light': '#fffbeb',
        'desc':  'Fellowships, training programmes, volunteering, contests, and special career opportunities in Nepal.',
        'tips':  [
            'Fellowship deadlines are strict — plan ahead',
            'Volunteering boosts your CV and network',
            'Look for opportunities aligned with your long-term goals',
        ],
    },
}


def _apply_filters(queryset, request):
    """Apply common GET filters to a Job queryset."""
    q        = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    exp      = request.GET.get('experience', '').strip()
    tags     = request.GET.getlist('tags')
    posted   = request.GET.get('posted_within', '').strip()
    sort     = request.GET.get('sort', 'deadline')

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(organization__icontains=q) |
            Q(description__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    if location:
        queryset = queryset.filter(location=location)

    if job_type:
        queryset = queryset.filter(job_type=job_type)

    if exp:
        queryset = queryset.filter(experience_level=exp)

    if tags:
        for tag in tags:
            queryset = queryset.filter(tags__slug=tag)

    if posted:
        try:
            days = int(posted)
            cutoff = timezone.now() - datetime.timedelta(days=days)
            queryset = queryset.filter(date_posted__gte=cutoff)
        except ValueError:
            pass

    if sort == 'newest':
        queryset = queryset.order_by('-date_posted')
    elif sort == 'views':
        queryset = queryset.order_by('-views')
    else:
        queryset = queryset.order_by('deadline', '-date_posted')

    return queryset, q, sort


def _saved_ids(request):
    if request.user.is_authenticated:
        return set(SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True))
    return set()


def _split_by_deadline(jobs_qs):
    today = timezone.now().date()
    jobs  = list(jobs_qs)
    active  = [j for j in jobs if j.deadline is None or j.deadline >= today]
    expired = [j for j in jobs if j.deadline is not None and j.deadline < today]
    return active, expired


def home(request):
    today = timezone.now().date()

    featured_jobs = list(Job.objects.filter(
        is_active=True, is_featured=True
    ).filter(
        models.Q(deadline__gte=today) | models.Q(deadline__isnull=True)
    ).prefetch_related('tags')[:6])

    urgent_jobs = list(Job.objects.filter(
        is_active=True,
        deadline__gte=today,
        deadline__lte=today + datetime.timedelta(days=7)
    ).order_by('deadline').prefetch_related('tags')[:8])

    latest_jobs = list(Job.objects.filter(is_active=True).filter(
        models.Q(deadline__gte=today) | models.Q(deadline__isnull=True)
    ).order_by('-date_posted').prefetch_related('tags')[:6])

    try:
        from blog.models import BlogPost
        latest_posts = list(BlogPost.objects.all()[:3])
    except Exception:
        latest_posts = []

    alert_form = JobAlertForm()

    context = {
        'featured_jobs':    featured_jobs,
        'urgent_jobs':      urgent_jobs,
        'latest_jobs':      latest_jobs,
        'latest_posts':     latest_posts,
        'categories_meta':  CATEGORY_META,
        'alert_form':       alert_form,
        'popular_tags':     Tag.objects.annotate(job_count=Count('jobs')).order_by('-job_count')[:12],
    }
    return render(request, 'jobs/home.html', context)


def category_page(request, category_slug):
    if category_slug not in CATEGORY_META:
        from django.http import Http404
        raise Http404
    meta = CATEGORY_META[category_slug]

    base_qs = Job.objects.filter(is_active=True, category=category_slug).prefetch_related('tags')
    filtered_qs, query, sort = _apply_filters(base_qs, request)

    active, expired = _split_by_deadline(filtered_qs)
    jobs_list = active + expired

    popular_tags = (Tag.objects.filter(jobs__category=category_slug, jobs__is_active=True)
                    .annotate(c=Count('jobs')).order_by('-c')[:10])

    alert_form = JobAlertForm(initial={'categories': [category_slug]})

    context = {
        'jobs':          jobs_list,
        'meta':          meta,
        'category_slug': category_slug,
        'query':         query,
        'sort':          sort,
        'saved_job_ids': _saved_ids(request),
        'total_count':   len(jobs_list),
        'related_cats':  {k: v for k, v in CATEGORY_META.items() if k != category_slug},
        'popular_tags':  popular_tags,
        'alert_form':    alert_form,
        # Province filter only makes sense for employment categories
        'province_choices': PROVINCE_CHOICES if category_slug in ('government', 'loksewa', 'private') else [],
        'job_type_choices': JobType.choices,
        'exp_choices':   ExperienceLevel.choices,
        'active_filters': {
            'location':  request.GET.get('location', ''),
            'job_type':  request.GET.get('job_type', ''),
            'experience': request.GET.get('experience', ''),
            'tags':      request.GET.getlist('tags'),
            'posted_within': request.GET.get('posted_within', ''),
        },
    }
    return render(request, 'jobs/category.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    Job.objects.filter(pk=pk).update(views=F('views') + 1)

    related = (Job.objects.filter(is_active=True, category=job.category, deadline__gte=timezone.now().date())
               .exclude(pk=pk).prefetch_related('tags')[:4])

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    context = {
        'job':           job,
        'is_saved':      is_saved,
        'related':       related,
        'saved_job_ids': _saved_ids(request),
        'meta':          CATEGORY_META.get(job.category, {}),
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def save_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
        messages.info(request, f'Removed "{job.title}" from saved jobs.')
    else:
        messages.success(request, f'"{job.title}" saved to your list.')
    return redirect(request.GET.get('next', '/'))


@login_required
def saved_jobs(request):
    saved = SavedJob.objects.filter(user=request.user).select_related('job').prefetch_related('job__tags').order_by('-saved_at')
    return render(request, 'jobs/saved_jobs.html', {
        'saved_jobs':    saved,
        'saved_job_ids': {s.job_id for s in saved},
    })


def search_view(request):
    base_qs = Job.objects.filter(is_active=True).prefetch_related('tags')
    category = request.GET.get('category', '').strip()

    if category and category in CATEGORY_META:
        base_qs = base_qs.filter(category=category)

    filtered_qs, query, sort = _apply_filters(base_qs, request)
    active, expired = _split_by_deadline(filtered_qs)

    context = {
        'jobs':           active + expired,
        'query':          query,
        'category':       category,
        'saved_job_ids':  _saved_ids(request),
        'total_count':    len(active) + len(expired),
        'categories_meta': CATEGORY_META,
        'popular_tags':   Tag.objects.annotate(c=Count('jobs')).order_by('-c')[:10],
        'province_choices': PROVINCE_CHOICES,
        'job_type_choices': JobType.choices,
        'exp_choices':    ExperienceLevel.choices,
        'active_filters': {
            'location':  request.GET.get('location', ''),
            'job_type':  request.GET.get('job_type', ''),
            'experience': request.GET.get('experience', ''),
            'tags':      request.GET.getlist('tags'),
            'posted_within': request.GET.get('posted_within', ''),
        },
    }
    return render(request, 'jobs/search_results.html', context)


def subscribe_alerts(request):
    if request.method == 'POST':
        form = JobAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(user=request.user if request.user.is_authenticated else None)
            if not alert.is_verified:
                _send_verification_email(request, alert)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'message': 'Subscribed! Check your email to verify.'})
            messages.success(request, 'Subscribed! Check your email to confirm your job alerts.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'errors': form.errors})
            messages.error(request, 'Please enter a valid email address.')
    return redirect(request.GET.get('next', '/'))


def _send_verification_email(request, alert):
    verify_url = request.build_absolute_uri(f'/alerts/verify/{alert.verification_token}/')
    send_mail(
        subject='Confirm your NepHub job alerts',
        message=(
            f'Hi,\n\n'
            f'Click the link below to confirm your job alert subscription on NepHub:\n\n'
            f'{verify_url}\n\n'
            f'If you did not sign up for job alerts, you can safely ignore this email.\n\n'
            f'— NepHub Team'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[alert.email],
        fail_silently=True,
    )


def verify_alert(request, token):
    try:
        alert = JobAlert.objects.get(verification_token=token)
        alert.is_verified = True
        alert.save()
        messages.success(request, 'Email verified! You will now receive job alerts.')
    except JobAlert.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('/')


@login_required
def recommendations(request):
    """CV/profile-based job recommendations."""
    try:
        profile = request.user.profile
    except Exception:
        return redirect('profile')

    keywords = set()
    if profile.bio:
        import re
        words = re.findall(r'\b[a-zA-Z]{4,}\b', profile.bio.lower())
        keywords = set(words)

    # Also match against the user's saved job tags
    saved_tags = set(
        Tag.objects.filter(jobs__saved_by__user=request.user).values_list('name', flat=True)
    )

    # Score jobs by keyword + tag overlap
    today = timezone.now().date()
    candidate_jobs = (Job.objects.filter(is_active=True, deadline__gte=today)
                      .prefetch_related('tags').exclude(saved_by__user=request.user))

    scored = []
    for job in candidate_jobs:
        score = 0
        job_text = f"{job.title} {job.organization} {job.description}".lower()
        for kw in keywords:
            if kw in job_text:
                score += 1
        for tag in job.tags.all():
            if tag.name.lower() in keywords or tag.name in saved_tags:
                score += 3
        if score > 0:
            scored.append((score, job))

    scored.sort(key=lambda x: -x[0])
    recommended = [j for _, j in scored[:10]]

    return render(request, 'jobs/recommendations.html', {
        'recommended':     recommended,
        'saved_job_ids':   _saved_ids(request),
        'has_bio':         bool(profile.bio),
        'categories_meta': CATEGORY_META,
    })


# ══════════════════════════════════════════════════════════════════
#   SITE ADMIN PANEL  (superuser only)
# ══════════════════════════════════════════════════════════════════

def _admin_ctx(extra=None):
    """Base context shared by all admin views."""
    from .models import AdInquiry
    from accounts.models import CVReviewRequest
    ctx = {
        'total_jobs':       Job.objects.count(),
        'active_jobs':      Job.objects.filter(is_active=True).count(),
        'featured_jobs':    Job.objects.filter(is_featured=True).count(),
        'expired_jobs':     Job.objects.filter(deadline__lt=timezone.now().date()).count(),
        'new_inquiry_count': AdInquiry.objects.filter(status='new').count(),
        'new_cv_request_count': CVReviewRequest.objects.filter(status='new').count(),
    }
    if extra:
        ctx.update(extra)
    return ctx


@superuser_required
def site_admin_dashboard(request):
    today = timezone.now().date()
    cat_stats = []
    for slug, meta in CATEGORY_META.items():
        cat_stats.append({
            'slug':    slug,
            'label':   meta['label'],
            'color':   meta['color'],
            'icon':    meta['icon'],
            'active':  Job.objects.filter(is_active=True, category=slug, deadline__gte=today).count(),
            'expired': Job.objects.filter(category=slug, deadline__lt=today).count(),
            'total':   Job.objects.filter(category=slug).count(),
        })
    recent_jobs = Job.objects.order_by('-date_posted')[:8]
    ctx = _admin_ctx({
        'cat_stats':   cat_stats,
        'recent_jobs': recent_jobs,
        'urgent_jobs': Job.objects.filter(
            is_active=True, deadline__gte=today,
            deadline__lte=today + datetime.timedelta(days=3)
        ).count(),
        'page_title':  'Dashboard',
    })
    return render(request, 'jobs/admin/dashboard.html', ctx)


@superuser_required
def site_admin_jobs(request):
    qs = Job.objects.prefetch_related('tags').order_by('-date_posted')

    # Filters
    category = request.GET.get('category', '')
    status   = request.GET.get('status', '')
    q        = request.GET.get('q', '')

    if category:
        qs = qs.filter(category=category)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status == 'expired':
        qs = qs.filter(deadline__lt=timezone.now().date())
    elif status == 'featured':
        qs = qs.filter(is_featured=True)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(organization__icontains=q))

    paginator = Paginator(qs, 25)
    page      = paginator.get_page(request.GET.get('page'))

    ctx = _admin_ctx({
        'jobs':            page,
        'page_obj':        page,
        'categories_meta': CATEGORY_META,
        'category_filter': category,
        'status_filter':   status,
        'q':               q,
        'page_title':      'All Jobs',
    })
    return render(request, 'jobs/admin/job_list.html', ctx)


@superuser_required
def site_admin_job_add(request):
    writer_notes = None
    if request.method == 'POST':
        form = AdminJobForm(request.POST)
        if form.is_valid():
            job = form.save()
            request.session.pop('writer_draft', None)
            messages.success(request, f'Job "{job.title}" added successfully.')
            return redirect('admin_jobs')
    else:
        draft = request.session.get('writer_draft')
        if draft:
            writer_notes = draft.pop('confidence_notes', '')
            form = AdminJobForm(initial=draft)
        else:
            form = AdminJobForm()
    ctx = _admin_ctx({
        'form': form,
        'page_title': 'Add Job',
        'is_edit': False,
        'writer_notes': writer_notes,
    })
    return render(request, 'jobs/admin/job_form.html', ctx)


@superuser_required
def site_admin_writer(request):
    """AI Writer — admin drops a screenshot/PDF/text/URL, Claude drafts the listing."""
    from .ai_writer import extract_job_draft, WriterError

    error = None
    if request.method == 'POST':
        try:
            draft = extract_job_draft(
                uploaded_file=request.FILES.get('source_file'),
                pasted_text=request.POST.get('pasted_text', ''),
                url=request.POST.get('source_url', ''),
            )
            request.session['writer_draft'] = draft
            messages.success(
                request,
                'Draft ready — review every field below, then hit Create Job to publish.'
            )
            return redirect('admin_job_add')
        except WriterError as exc:
            error = str(exc)
        except Exception:
            logger.exception('AI Writer failed')
            error = 'Something went wrong while drafting. Try again or use a different input.'

    ctx = _admin_ctx({'page_title': 'AI Writer', 'error': error})
    return render(request, 'jobs/admin/writer.html', ctx)


@superuser_required
def site_admin_job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        form = AdminJobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f'Job "{job.title}" updated.')
            return redirect('admin_jobs')
    else:
        form = AdminJobForm(instance=job)
    ctx = _admin_ctx({'form': form, 'job': job, 'page_title': f'Edit: {job.title}', 'is_edit': True})
    return render(request, 'jobs/admin/job_form.html', ctx)


@superuser_required
def site_admin_job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        title = job.title
        job.delete()
        messages.success(request, f'Job "{title}" deleted.')
        return redirect('admin_jobs')
    ctx = _admin_ctx({'job': job, 'page_title': 'Delete Job'})
    return render(request, 'jobs/admin/job_confirm_delete.html', ctx)


@superuser_required
def site_admin_job_toggle(request, pk, field):
    job = get_object_or_404(Job, pk=pk)
    if field == 'active':
        job.is_active = not job.is_active
        job.save(update_fields=['is_active'])
    elif field == 'featured':
        job.is_featured = not job.is_featured
        job.save(update_fields=['is_featured'])
    return redirect(request.GET.get('next', 'admin_jobs'))


# ── Admin: Ad Inquiries ────────────────────────────────────────────
@superuser_required
def site_admin_inquiries(request):
    from .models import AdInquiry
    status_filter = request.GET.get('status', '')
    qs = AdInquiry.objects.all()
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator   = Paginator(qs, 25)
    page_obj    = paginator.get_page(request.GET.get('page'))
    new_count   = AdInquiry.objects.filter(status='new').count()

    ctx = _admin_ctx({
        'inquiries':     page_obj,
        'page_obj':      page_obj,
        'status_filter': status_filter,
        'new_count':     new_count,
    })
    return render(request, 'jobs/admin/inquiries.html', ctx)


@superuser_required
def site_admin_inquiry_status(request, pk):
    from .models import AdInquiry
    if request.method != 'POST':
        return redirect('admin_inquiries')
    inquiry = get_object_or_404(AdInquiry, pk=pk)
    new_status = request.POST.get('status', 'new')
    if new_status in ('new', 'contacted', 'closed'):
        inquiry.status = new_status
        inquiry.save(update_fields=['status'])
        messages.success(request, f'Inquiry from {inquiry.company_name} marked as {new_status}.')
    return redirect('admin_inquiries')


# ── Admin: Users ───────────────────────────────────────────────────
@superuser_required
def site_admin_users(request):
    from django.contrib.auth.models import User
    q = request.GET.get('q', '')
    qs = User.objects.select_related('profile').order_by('-date_joined')
    if q:
        qs = qs.filter(
            Q(username__icontains=q) | Q(email__icontains=q)
        )

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = _admin_ctx({
        'users':    page_obj,
        'page_obj': page_obj,
        'q':        q,
        'total_users': User.objects.count(),
    })
    return render(request, 'jobs/admin/users.html', ctx)


@superuser_required
def site_admin_user_toggle_super(request, pk):
    """Promote or demote a user to/from superuser."""
    from django.contrib.auth.models import User
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        # Never demote yourself
        if target == request.user:
            messages.error(request, "You can't change your own superuser status.")
        else:
            target.is_superuser = not target.is_superuser
            target.is_staff     = target.is_superuser
            target.save(update_fields=['is_superuser', 'is_staff'])
            action = 'promoted to admin' if target.is_superuser else 'demoted to regular user'
            messages.success(request, f'{target.username} {action}.')
    return redirect('admin_users')


# ── Admin: Subscribers ─────────────────────────────────────────────
@superuser_required
def site_admin_subscribers(request):
    status_filter = request.GET.get('status', '')
    qs = JobAlert.objects.order_by('-created_at')
    if status_filter == 'verified':
        qs = qs.filter(is_verified=True)
    elif status_filter == 'unverified':
        qs = qs.filter(is_verified=False)

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = _admin_ctx({
        'subscribers':    page_obj,
        'page_obj':       page_obj,
        'status_filter':  status_filter,
        'total_verified': JobAlert.objects.filter(is_verified=True).count(),
        'total_subs':     JobAlert.objects.count(),
    })
    return render(request, 'jobs/admin/subscribers.html', ctx)


# ── Admin: CV Review Requests ──────────────────────────────────────
@superuser_required
def site_admin_cv_requests(request):
    from accounts.models import CVReviewRequest
    status_filter = request.GET.get('status', '')
    qs = (CVReviewRequest.objects
          .select_related('user', 'user__profile')
          .order_by('-created_at'))
    if status_filter in ('new', 'in_review', 'completed'):
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = _admin_ctx({
        'cv_requests':   page_obj,
        'page_obj':      page_obj,
        'status_filter': status_filter,
        'total_new':     CVReviewRequest.objects.filter(status='new').count(),
        'total_all':     CVReviewRequest.objects.count(),
    })
    return render(request, 'jobs/admin/cv_requests.html', ctx)


@superuser_required
def site_admin_cv_request_status(request, pk):
    from accounts.models import CVReviewRequest
    if request.method != 'POST':
        return redirect('admin_cv_requests')
    req = get_object_or_404(CVReviewRequest, pk=pk)
    new_status = request.POST.get('status', 'new')
    if new_status in ('new', 'in_review', 'completed'):
        req.status = new_status
        notes = request.POST.get('admin_notes')
        if notes is not None:
            req.admin_notes = notes.strip()
        req.save(update_fields=['status', 'admin_notes', 'updated_at'])
        messages.success(request, f'CV review for {req.user.username} marked as {req.get_status_display()}.')
    return redirect('admin_cv_requests')
