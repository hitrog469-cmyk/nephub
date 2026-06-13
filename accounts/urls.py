from django.urls import path
from . import views

urlpatterns = [
    path('signup/',                      views.signup_view,            name='signup'),
    path('verify-code/',                 views.verify_code_view,       name='verify_code'),
    path('resend-code/',                 views.resend_code_view,       name='resend_code'),
    path('login/',                       views.login_view,             name='login'),
    path('logout/',                      views.logout_view,            name='logout'),
    path('post-login/',                  views.post_login_view,        name='post_login'),
    path('choose-username/',             views.choose_username_view,   name='choose_username'),
    path('check-username/',              views.check_username_view,    name='check_username'),
    path('profile/',                     views.profile_view,           name='profile'),
    path('profile/cv-review/',           views.request_cv_review,      name='request_cv_review'),
]
