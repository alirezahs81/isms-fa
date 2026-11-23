from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction, connection
from django.utils import timezone

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

    def clean(self):
        super().clean()
        errors = {}
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = 'مبلغ فاکتور باید بیشتر از صفر باشد.'
        if self.discount is not None and self.discount < 0:
            errors['discount'] = 'تخفیف نمی‌تواند منفی باشد.'
        if self.amount is not None and self.discount is not None and self.discount > self.amount:
            errors['discount'] = 'تخفیف نمی‌تواند از مبلغ فاکتور بیشتر باشد.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            with transaction.atomic():
                # Serialize invoice number allocation on PostgreSQL.
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [731904221])
                year = timezone.localdate().strftime('%Y')
                prefix = f'INV-{year}-'
                last_number = 0
                last = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
                if last:
                    try:
                        last_number = int(last.invoice_number.rsplit('-', 1)[1])
                    except (IndexError, ValueError):
                        raise ValidationError({'invoice_number': 'شماره فاکتور قبلی نامعتبر است.'})
                self.invoice_number = f'{prefix}{last_number + 1:04d}'
                self.full_clean()
                return super().save(*args, **kwargs)
        self.full_clean()
        return super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        errors = {}
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = 'مبلغ پرداخت باید بیشتر از صفر باشد.'
        if self.invoice_id and self.amount is not None:
            invoice = self.invoice
            paid = invoice.payments.exclude(pk=self.pk).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            if invoice.status == 'cancelled':
                errors['invoice'] = 'ثبت پرداخت برای فاکتور ابطال‌شده مجاز نیست.'
            elif self.amount > invoice.total - paid:
                errors['amount'] = 'مبلغ پرداخت از مانده فاکتور بیشتر است.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(pk=self.invoice_id)
            self.invoice = invoice
            self.full_clean()
            result = super().save(*args, **kwargs)
            paid_sum = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            new_status = 'paid' if paid_sum >= invoice.total else 'unpaid'
            if invoice.status != 'cancelled' and invoice.status != new_status:
                Invoice.objects.filter(pk=invoice.pk).update(status=new_status)
            return result

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(pk=self.invoice_id)
            result = super().delete(*args, **kwargs)
            paid_sum = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            new_status = 'paid' if paid_sum >= invoice.total else 'unpaid'
            if invoice.status != 'cancelled' and invoice.status != new_status:
                Invoice.objects.filter(pk=invoice.pk).update(status=new_status)
            return result

    def __str__(self):
        return f'{self.invoice.invoice_number} — {self.amount}'
