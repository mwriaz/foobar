from django.contrib import admin
from django.urls import path
from skill_test import views

urlpatterns = [
    path("", views.index, name='skill_test')
    
]