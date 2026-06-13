import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # Block only *verified* (active) accounts. Abandoned, unverified
        # signups with this email are cleaned up in the view so the address
        # can be reused.
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError(
                'An account with this email already exists. Please log in instead.'
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Rich profile form — personal info + CV."""

    class Meta:
        model   = UserProfile
        fields  = ('full_name', 'phone', 'location', 'experience',
                   'bio', 'linkedin_url', 'website_url', 'cv')
        widgets = {
            'full_name':    forms.TextInput(attrs={
                'placeholder': 'e.g. Ramesh Sharma',
                'class': 'form-input',
            }),
            'phone':        forms.TextInput(attrs={
                'placeholder': '98XXXXXXXX',
                'class': 'form-input',
            }),
            'location':     forms.TextInput(attrs={
                'placeholder': 'e.g. Kathmandu, Bagmati Province',
                'class': 'form-input',
            }),
            'experience':   forms.Select(attrs={'class': 'form-input'}),
            'bio':          forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Brief intro — skills, interests, career goals…',
                'class': 'form-input',
            }),
            'linkedin_url': forms.URLInput(attrs={
                'placeholder': 'https://linkedin.com/in/yourprofile',
                'class': 'form-input',
            }),
            'website_url':  forms.URLInput(attrs={
                'placeholder': 'https://your-portfolio.com',
                'class': 'form-input',
            }),
            'cv':           forms.FileInput(attrs={
                'accept': '.pdf,.doc,.docx',
                'class': 'form-input',
            }),
        }

    CV_ALLOWED_EXTENSIONS = ('.pdf', '.doc', '.docx')
    CV_MAX_SIZE = 5 * 1024 * 1024  # 5 MB

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv and hasattr(cv, 'size'):
            import os as _os
            ext = _os.path.splitext(cv.name)[1].lower()
            if ext not in self.CV_ALLOWED_EXTENSIONS:
                raise forms.ValidationError('CV must be a PDF, DOC or DOCX file.')
            if cv.size > self.CV_MAX_SIZE:
                raise forms.ValidationError('CV file too large — maximum 5 MB.')
        return cv


class UsernameForm(forms.Form):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. rohit_sharma',
            'autofocus': True,
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError('Only letters, numbers and underscores allowed.')
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken. Try another.')
        return username


# Keep old alias so nothing breaks if imported elsewhere
CVUploadForm = ProfileForm
