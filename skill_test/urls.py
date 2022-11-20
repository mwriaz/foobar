from django.contrib import admin
from django.urls import path
from skill_test import views

urlpatterns = [
    path("", views.index, name='skill_test'),
    path('logout/', views.logout_view, name='logout'),
    path('test_manage/', views.test_manage, name='test_manage'),
    path('tests/', views.tests, name='tests'),
    path('results/', views.results, name='results'),
    path('users_m/', views.users_m, name='users_m'),
    path('take_test/', views.take_test, name='take_test'),
    path("/(?P<t_id>\w+)/$", views.take_test, name='take_test')
    
    
]