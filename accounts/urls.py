from django.urls import path
from . import views

urlpatterns = [
    path('signup/',                      views.signup_view,            name='signup'),
    path('verification-sent/',           views.verification_sent_view, name='verification_sent'),
    path('verify-email/<str:token>/',    views.verify_email_view,      name='verify_email'),
    path('login/',                       views.login_view,             name='login'),
    path('logout/',                      views.logout_view,            name='logout'),
    path('post-login/',                  views.post_login_view,        name='post_login'),
    path('choose-username/',             views.choose_username_view,   name='choose_username'),
    path('check-username/',              views.check_username_view,    name='check_username'),
    path('profile/',                     views.profile_view,           name='profile'),
]
