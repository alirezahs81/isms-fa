from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Customer, ServicePlan, ServiceOrder


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'email', 'national_code', 'company', 'address', 'notes']
        labels = {
            'full_name': 'نام و نام خانوادگی', 'phone': 'موبایل', 'email': 'ایمیل',
            'national_code': 'کد ملی', 'company': 'شرکت/سازمان', 'address': 'آدرس', 'notes': 'یادداشت',
        }


class PlanForm(forms.ModelForm):
    class Meta:
        model = ServicePlan
        fields = ['name', 'category', 'duration_months', 'price', 'specs', 'is_active']
        labels = {
            'name': 'نام پلن', 'category': 'دسته‌بندی', 'duration_months': 'مدت',
            'price': 'قیمت (تومان)', 'specs': 'مشخصات', 'is_active': 'فعال',
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = ['customer', 'plan', 'start_date', 'end_date', 'status', 'account_info', 'notes']
        labels = {
            'customer': 'مشتری', 'plan': 'پلن', 'start_date': 'تاریخ شروع', 'end_date': 'تاریخ پایان',
            'status': 'وضعیت', 'account_info': 'اطلاعات حساب', 'notes': 'یادداشت',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


@login_required
def customer_list(request):
    q = request.GET.get('q', '').strip()
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(full_name__icontains=q) | customers.filter(phone__icontains=q)
    return render(request, 'services/customers.html', {'customers': customers, 'q': q})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'services/customer_detail.html', {
        'customer': customer,
        'orders': customer.orders.select_related('plan'),
        'invoices': customer.invoices.select_related('plan'),
    })


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'مشتری با موفقیت ثبت شد.')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'form.html', {'form': form, 'title': 'ثبت مشتری جدید'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات مشتری به‌روزرسانی شد.')
            return redirect('customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'form.html', {'form': form, 'title': f'ویرایش: {customer}'})


@login_required
def plan_list(request):
    return render(request, 'services/plans.html', {'plans': ServicePlan.objects.all()})


@login_required
def plan_create(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'پلن جدید ثبت شد.')
            return redirect('plan_list')
    else:
        form = PlanForm()
    return render(request, 'form.html', {'form': form, 'title': 'پلن سرویس جدید'})


@login_required
def order_list(request):
    orders = ServiceOrder.objects.select_related('customer', 'plan')
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'services/orders.html', {'orders': orders, 'status': status})


@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if not order.end_date:
                order.end_date = order.start_date + timedelta(days=30 * order.plan.duration_months)
            order.save()
            messages.success(request, 'سرویس با موفقیت ثبت شد.')
            return redirect('order_list')
    else:
        form = OrderForm(initial={'start_date': timezone.localdate()})
    return render(request, 'form.html', {'form': form, 'title': 'ثبت سرویس جدید'})


@login_required
def order_renew(request, pk):
    """تمدید سرویس: تمدید یک دوره از تاریخ پایان فعلی"""
    order = get_object_or_404(ServiceOrder, pk=pk)
    order.end_date = order.end_date + timedelta(days=30 * order.plan.duration_months)
    order.status = 'active'
    order.save()
    messages.success(request, f'سرویس تا {order.end_date} تمدید شد.')
    return redirect('order_list')
