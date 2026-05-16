from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

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


# Keep old alias so nothing breaks if imported elsewhere
CVUploadForm = ProfileForm
