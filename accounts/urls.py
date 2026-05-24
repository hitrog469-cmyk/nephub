from django.urls import path
from . import views

urlpatterns = [
    path('signup/',                      views.signup_view,           name='signup'),
    path('verification-sent/',           views.verification_sent_view, name='verification_sent'),
    path('verify-email/<str:token>/',    views.verify_email_view,     name='verify_email'),
    path('login/',                       views.login_view,            name='login'),
    path('logout/',                      views.logout_view,           name='logout'),
    path('profile/',                     views.profile_view,          name='profile'),
]
