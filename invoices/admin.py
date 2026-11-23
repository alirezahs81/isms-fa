from django.contrib import admin
from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'plan', 'amount', 'discount', 'total', 'status', 'issue_date']
    list_filter = ['status']
    search_fields = ['invoice_number', 'customer__full_name']
    readonly_fields = [field.name for field in Invoice._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return super().has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'method', 'paid_at', 'recorded_by']
    list_filter = ['method']
    readonly_fields = [field.name for field in Payment._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return super().has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False
