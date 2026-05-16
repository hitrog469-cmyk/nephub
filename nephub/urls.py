from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Our custom accounts views (login, signup, logout, profile) — matched FIRST
    path('accounts/', include('accounts.urls')),

    # allauth handles the Google OAuth flow:
    #   /accounts/google/login/           → starts Google OAuth
    #   /accounts/google/login/callback/  → Google redirects here
    # Our custom login/signup at accounts/ still take precedence above.
    path('accounts/', include('allauth.urls')),

    path('blog/', include('blog.urls')),
    path('', include('pages.urls')),
    path('', include('jobs.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
