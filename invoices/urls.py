from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('invoices/', views.invoice_list, name='list'),
    path('invoices/add/', views.invoice_create, name='create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='detail'),
    path('invoices/<int:pk>/cancel/', views.invoice_cancel, name='cancel'),
    path('orders/<int:order_pk>/invoice/', views.invoice_from_order, name='from_order'),
]
