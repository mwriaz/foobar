from django.contrib import admin
from django.urls import path
from skill_test import views

urlpatterns = [
    path("", views.index, name='skill_test'),
    path('logout/', views.logout_view, name='logout'),
    path('test_manage/', views.test_manage, name='test_manage')
    
]