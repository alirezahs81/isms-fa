from django.contrib import admin
from .models import Invoice, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'plan', 'amount', 'discount', 'total', 'status', 'issue_date']
    list_filter = ['status']
    search_fields = ['invoice_number', 'customer__full_name']
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'method', 'paid_at', 'recorded_by']
    list_filter = ['method']
