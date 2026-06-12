from django import forms
from .models import Job, JobAlert, Category, Tag, PROVINCE_CHOICES, JobType, ExperienceLevel


class JobAlertForm(forms.ModelForm):
    categories = forms.MultipleChoiceField(
        choices=Category.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Job Categories',
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Skills / Keywords',
    )

    class Meta:
        model = JobAlert
        fields = ('email', 'categories', 'tags')
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
        }

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        instance.subscribed_categories = self.cleaned_data.get('categories', [])
        if user and user.is_authenticated:
            instance.user = user
            instance.email = user.email
            instance.is_verified = True
        import secrets
        instance.verification_token = secrets.token_urlsafe(32)
        if commit:
            instance.save()
            instance.tags.set(self.cleaned_data.get('tags', []))
        return instance


class JobFilterForm(forms.Form):
    q            = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search...'}))
    category     = forms.ChoiceField(choices=[('', 'All Categories')] + list(Category.choices), required=False)
    location     = forms.ChoiceField(choices=[('', 'All Locations')] + PROVINCE_CHOICES, required=False)
    job_type     = forms.ChoiceField(choices=[('', 'All Types')] + list(JobType.choices), required=False)
    experience   = forms.ChoiceField(choices=[('', 'Any Experience')] + list(ExperienceLevel.choices), required=False)
    tags         = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)
    posted_within = forms.ChoiceField(
        choices=[('', 'Any Time'), ('1', 'Today'), ('3', 'Last 3 Days'), ('7', 'Last Week'), ('30', 'Last Month')],
        required=False,
    )


# ── Admin Job Form ─────────────────────────────────────────────────
class AdminJobForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Tags / Keywords',
    )
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'admin-input'}),
        help_text='Leave blank for open/rolling opportunities with no deadline.',
    )

    class Meta:
        model  = Job
        fields = [
            'title', 'organization', 'category', 'job_type',
            'experience_level', 'location', 'description', 'requirements',
            'deadline', 'apply_link', 'source',
            'salary_min', 'salary_max',
            'is_active', 'is_featured',
            'tags',
        ]
        widgets = {
            'title':          forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'Job title'}),
            'organization':   forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'Hiring organisation'}),
            'category':       forms.Select(attrs={'class': 'admin-input'}),
            'job_type':       forms.Select(attrs={'class': 'admin-input'}),
            'experience_level': forms.Select(attrs={'class': 'admin-input'}),
            'location':       forms.Select(attrs={'class': 'admin-input'}),
            'description':    forms.Textarea(attrs={'class': 'admin-input', 'rows': 6, 'placeholder': 'Full job description…'}),
            'requirements':   forms.Textarea(attrs={'class': 'admin-input', 'rows': 4, 'placeholder': 'Requirements and qualifications…'}),
            'apply_link':     forms.URLInput(attrs={'class': 'admin-input', 'placeholder': 'https://'}),
            'source':         forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'e.g. moald.gov.np'}),
            'salary_min':     forms.NumberInput(attrs={'class': 'admin-input', 'placeholder': 'Min monthly (NPR)'}),
            'salary_max':     forms.NumberInput(attrs={'class': 'admin-input', 'placeholder': 'Max monthly (NPR)'}),
        }
