from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('reports/', views.reports, name='reports'),
]
