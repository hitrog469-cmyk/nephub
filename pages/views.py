from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from jobs.models import Job, AdInquiry
from accounts.throttle import rate_limit


def about_view(request):
    stats = {
        'total_jobs':    Job.objects.filter(is_active=True).count(),
        'categories':    7,
        'organizations': Job.objects.filter(is_active=True).values('organization').distinct().count(),
    }
    return render(request, 'pages/about.html', {'stats': stats})


def cv_page_view(request):
    return render(request, 'pages/cv_page.html')


@rate_limit('inquiry', max_attempts=5, window_seconds=3600)
def advertise_view(request):
    if request.method == 'POST':
        # Honeypot — real users never see or fill this field; bots do.
        if request.POST.get('website', ''):
            return redirect('advertise')

        company_name = request.POST.get('company_name', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        email        = request.POST.get('email', '').strip()
        phone        = request.POST.get('phone', '').strip()
        ad_type      = request.POST.get('ad_type', 'sidebar')
        msg          = request.POST.get('message', '').strip()

        if not company_name or not email:
            messages.error(request, 'Company name and email are required.')
            return render(request, 'pages/advertise.html', {'post': request.POST})

        # Save to database
        inquiry = AdInquiry.objects.create(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            ad_type=ad_type,
            message=msg,
        )

        # Email notification to admin
        ad_type_label = dict(AdInquiry.AD_TYPE_CHOICES).get(ad_type, ad_type)
        email_body = f"""New advertising inquiry on NepHub!

Company:  {company_name}
Contact:  {contact_name}
Email:    {email}
Phone:    {phone or '—'}
Ad Type:  {ad_type_label}

Message:
{msg or '(none)'}

---
View in admin: {request.build_absolute_uri('/dashboard/inquiries/')}
"""
        try:
            send_mail(
                subject=f'[NepHub] New Ad Inquiry — {company_name}',
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't break the flow if email fails

        messages.success(request, f'Thanks {contact_name or company_name}! We received your inquiry and will get back to you within 24 hours.')
        return redirect('advertise')

    return render(request, 'pages/advertise.html')
