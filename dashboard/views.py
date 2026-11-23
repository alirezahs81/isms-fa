from accounts.permissions import role_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from services.models import Customer, ServicePlan, ServiceOrder
from invoices.models import Invoice, Payment


def staff_required(view):
    """دسترسی فقط برای کارکنان (ادمین/کارمند)"""
    return staff_member_required(view)


@role_required('admin', 'finance')
def dashboard(request):
    today = timezone.localdate()
    soon = today + timedelta(days=14)

    active_orders = ServiceOrder.objects.filter(status='active')
    expiring = active_orders.filter(end_date__lte=soon).order_by('end_date')
    month_income = sum(p.amount for p in Payment.objects.filter(paid_at__month=today.month, paid_at__year=today.year))
    unpaid_invoices = Invoice.objects.filter(status='unpaid')

    context = {
        'customer_count': Customer.objects.count(),
        'active_count': active_orders.count(),
        'plan_count': ServicePlan.objects.filter(is_active=True).count(),
        'month_income': month_income,
        'expiring_orders': expiring,
        'unpaid_invoices': unpaid_invoices[:8],
    }
    return render(request, 'dashboard.html', context)


@staff_member_required
def reports(request):
    today = timezone.localdate()
    income_by_month = {}
    for p in Payment.objects.select_related('invoice'):
        key = p.paid_at.strftime('%Y-%m')
        income_by_month[key] = income_by_month.get(key, 0) + p.amount

    by_category = {}
    for order in ServiceOrder.objects.select_related('plan'):
        cat = order.plan.get_category_display()
        by_category[cat] = by_category.get(cat, 0) + 1

    context = {
        'income_by_month': sorted(income_by_month.items(), reverse=True),
        'by_category': by_category,
        'total_income': sum(income_by_month.values()),
        'unpaid_total': sum(inv.total for inv in Invoice.objects.filter(status='unpaid')),
        'active_orders': ServiceOrder.objects.filter(status='active').count(),
        'expired_orders': ServiceOrder.objects.filter(status='expired').count(),
    }
    return render(request, 'reports.html', context)
