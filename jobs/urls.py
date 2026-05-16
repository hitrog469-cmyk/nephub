from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                             views.home,            name='home'),
    path('jobs/<slug:category_slug>/',   views.category_page,   name='category_page'),
    path('job/<int:pk>/',                views.job_detail,      name='job_detail'),
    path('job/<int:pk>/save/',           views.save_job,        name='save_job'),
    path('saved/',                       views.saved_jobs,      name='saved_jobs'),
    path('search/',                      views.search_view,     name='search'),
    path('subscribe/',                   views.subscribe_alerts, name='subscribe_alerts'),
    path('verify-alert/<str:token>/',    views.verify_alert,    name='verify_alert'),
    path('recommendations/',             views.recommendations,  name='recommendations'),

    # ── Site Admin Panel (superuser only) ──────────────────────────
    path('dashboard/',
         views.site_admin_dashboard,        name='admin_dashboard'),
    path('dashboard/jobs/',
         views.site_admin_jobs,             name='admin_jobs'),
    path('dashboard/jobs/add/',
         views.site_admin_job_add,          name='admin_job_add'),
    path('dashboard/jobs/<int:pk>/edit/',
         views.site_admin_job_edit,         name='admin_job_edit'),
    path('dashboard/jobs/<int:pk>/delete/',
         views.site_admin_job_delete,       name='admin_job_delete'),
    path('dashboard/jobs/<int:pk>/toggle/<str:field>/',
         views.site_admin_job_toggle,       name='admin_job_toggle'),

    # Admin — Inquiries
    path('dashboard/inquiries/',
         views.site_admin_inquiries,        name='admin_inquiries'),
    path('dashboard/inquiries/<int:pk>/status/',
         views.site_admin_inquiry_status,   name='admin_inquiry_status'),

    # Admin — Users
    path('dashboard/users/',
         views.site_admin_users,            name='admin_users'),
    path('dashboard/users/<int:pk>/toggle-super/',
         views.site_admin_user_toggle_super, name='admin_user_toggle_super'),

    # Admin — Subscribers
    path('dashboard/subscribers/',
         views.site_admin_subscribers,      name='admin_subscribers'),
]
