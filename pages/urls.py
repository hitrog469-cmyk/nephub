from django.urls import path
from . import views

urlpatterns = [
    path('about/',     views.about_view,     name='about'),
    path('cv/',        views.cv_page_view,   name='cv_page'),
    path('advertise/', views.advertise_view, name='advertise'),
]
