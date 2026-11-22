from django.db import models
from django.utils import timezone
from decimal import Decimal
from services.models import Customer, ServicePlan


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'پرداخت نشده'),
        ('paid', 'پرداخت شده'),
        ('cancelled', 'ابطال شده'),
    ]

    invoice_number = models.CharField('شماره فاکتور', max_length=20, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices', verbose_name='مشتری')
    plan = models.ForeignKey(ServicePlan, on_delete=models.PROTECT, verbose_name='پلن')
    amount = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0)
    discount = models.DecimalField('تخفیف (تومان)', max_digits=12, decimal_places=0, default=0)
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES, default='unpaid')
    issue_date = models.DateField('تاریخ صدور', default=timezone.localdate)
    due_date = models.DateField('تاریخ سررسید', null=True, blank=True)
    notes = models.TextField('یادداشت', blank=True)
    order = models.ForeignKey('services.ServiceOrder', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='invoices', verbose_name='سفارش مرتبط')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name='صادرکننده')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        ordering = ['-issue_date', '-id']

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.localdate().strftime('%Y')
            last = Invoice.objects.filter(invoice_number__startswith=f'INV-{year}').count()
            self.invoice_number = f'INV-{year}-{last + 1:04d}'
        super().save(*args, **kwargs)

    @property
    def total(self):
        return self.amount - self.discount

    @property
    def is_paid(self):
        return self.status == 'paid'

    def __str__(self):
        return self.invoice_number


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'نقدی'),
        ('card', 'کارت به کارت'),
        ('online', 'درگاه آنلاین'),
        ('transfer', 'انتقال بانکی'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name='فاکتور')
    amount = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0)
    method = models.CharField('روش پرداخت', max_length=10, choices=METHOD_CHOICES, default='cash')
    paid_at = models.DateTimeField('تاریخ پرداخت', default=timezone.now)
    reference = models.CharField('شماره پیگیری/مرجع', max_length=100, blank=True)
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name='ثبت‌کننده')

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-paid_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        paid_sum = self.invoice.payments.aggregate(s=models.Sum('amount'))['s'] or Decimal('0')
        if paid_sum >= self.invoice.total:
            Invoice.objects.filter(pk=self.invoice.pk).exclude(status='paid').update(status='paid')

    def __str__(self):
        return f'{self.invoice.invoice_number} — {self.amount}'
