from django.contrib import admin
from .models import Customer, ServicePlan, ServiceOrder


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'company', 'created_at']
    search_fields = ['full_name', 'phone', 'national_code']


@admin.register(ServicePlan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'duration_months', 'price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']


@admin.register(ServiceOrder)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'plan', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'plan__category']
    search_fields = ['customer__full_name', 'account_info']
