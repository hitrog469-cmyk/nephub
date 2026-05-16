from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class Category(models.TextChoices):
    GOVERNMENT  = 'government',  'Government'
    LOKSEWA     = 'loksewa',     'Loksewa'
    PRIVATE     = 'private',     'Private'
    SCHOLARSHIP = 'scholarship', 'Scholarship'
    FOREIGN     = 'foreign',     'Foreign Employment'
    INTERNSHIP  = 'internship',  'Internship'
    OPPORTUNITY = 'opportunity', 'Opportunity'


class JobType(models.TextChoices):
    FULL_TIME   = 'full_time',   'Full Time'
    PART_TIME   = 'part_time',   'Part Time'
    CONTRACT    = 'contract',    'Contract'
    INTERNSHIP  = 'internship',  'Internship'


class ExperienceLevel(models.TextChoices):
    ENTRY  = 'entry',  'Entry Level'
    MID    = 'mid',    'Mid Level'
    SENIOR = 'senior', 'Senior Level'
    ANY    = 'any',    'Any Level'


PROVINCE_CHOICES = [
    ('koshi',       'Koshi Province'),
    ('madhesh',     'Madhesh Province'),
    ('bagmati',     'Bagmati Province'),
    ('gandaki',     'Gandaki Province'),
    ('lumbini',     'Lumbini Province'),
    ('karnali',     'Karnali Province'),
    ('sudurpashchim','Sudurpashchim Province'),
    ('remote',      'Remote / Work from Home'),
    ('nepal',       'Nepal (All)'),
]


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Job(models.Model):
    title            = models.CharField(max_length=300)
    organization     = models.CharField(max_length=200)
    category         = models.CharField(max_length=20, choices=Category.choices, default=Category.GOVERNMENT)
    job_type         = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME, blank=True)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ANY, blank=True)
    location         = models.CharField(max_length=20, choices=PROVINCE_CHOICES, default='nepal', blank=True)
    description      = models.TextField(blank=True)
    requirements     = models.TextField(blank=True)
    deadline         = models.DateField()
    apply_link       = models.URLField(max_length=500, blank=True)
    source           = models.CharField(max_length=200, blank=True)
    date_posted      = models.DateTimeField(default=timezone.now)
    is_active        = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)
    views            = models.PositiveIntegerField(default=0)
    salary_min       = models.PositiveIntegerField(null=True, blank=True, help_text='Monthly salary min (NPR)')
    salary_max       = models.PositiveIntegerField(null=True, blank=True, help_text='Monthly salary max (NPR)')
    tags             = models.ManyToManyField(Tag, blank=True, related_name='jobs')

    class Meta:
        ordering = ['deadline', '-date_posted']

    def __str__(self):
        return f"{self.title} — {self.organization}"

    @property
    def is_expired(self):
        return self.deadline < timezone.now().date()

    @property
    def days_left(self):
        return (self.deadline - timezone.now().date()).days

    @property
    def urgency_label(self):
        d = self.days_left
        if d < 0:  return 'expired'
        if d == 0: return 'today'
        if d <= 3: return 'urgent'
        if d <= 7: return 'soon'
        return 'open'

    @property
    def salary_display(self):
        if self.salary_min and self.salary_max:
            return f"NPR {self.salary_min:,} – {self.salary_max:,}/month"
        elif self.salary_min:
            return f"NPR {self.salary_min:,}+/month"
        return ""


class SavedJob(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job      = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} — {self.job.title}"


class JobAlert(models.Model):
    user                   = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE, related_name='job_alert')
    email                  = models.EmailField()
    subscribed_categories  = models.JSONField(default=list)
    tags                   = models.ManyToManyField(Tag, blank=True, related_name='alerts')
    is_active              = models.BooleanField(default=True)
    is_verified            = models.BooleanField(default=False)
    created_at             = models.DateTimeField(auto_now_add=True)
    verification_token     = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return f"Alert: {self.email}"

    def get_category_display_list(self):
        labels = dict(Category.choices)
        return [labels.get(c, c) for c in self.subscribed_categories]


class AdInquiry(models.Model):
    AD_TYPE_CHOICES = [
        ('sidebar',     'Sidebar Banner (300×250)'),
        ('banner',      'Leaderboard Banner (728×90)'),
        ('sponsored',   'Sponsored Job Listing'),
        ('newsletter',  'Newsletter / Email Blast'),
        ('brand',       'Brand Awareness / Homepage Feature'),
        ('product',     'Product or Service Promotion'),
        ('custom',      'Custom / Other'),
    ]
    STATUS_CHOICES = [
        ('new',       'New'),
        ('contacted', 'Contacted'),
        ('closed',    'Closed'),
    ]

    company_name  = models.CharField(max_length=150)
    contact_name  = models.CharField(max_length=100)
    email         = models.EmailField()
    phone         = models.CharField(max_length=20, blank=True)
    ad_type       = models.CharField(max_length=20, choices=AD_TYPE_CHOICES, default='sidebar')
    message       = models.TextField(blank=True,
                                     help_text='Tell us about your business and advertising goals')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes   = models.TextField(blank=True, help_text='Internal notes (not shown to advertiser)')
    submitted_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering  = ['-submitted_at']
        verbose_name        = 'Ad Inquiry'
        verbose_name_plural = 'Ad Inquiries'

    def __str__(self):
        return f"{self.company_name} ({self.submitted_at.date()})"
