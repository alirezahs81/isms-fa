from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from services.models import Customer, ServicePlan


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('unpaid', _('Unpaid')),
        ('paid', _('Paid')),
        ('cancelled', _('Cancelled')),
    ]

    invoice_number = models.CharField(_('Invoice number'), max_length=20, unique=True, blank=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='invoices', verbose_name=_('Customer')
    )
    plan = models.ForeignKey(ServicePlan, on_delete=models.PROTECT, verbose_name=_('Plan'))
    amount = models.DecimalField(_('Amount (Toman)'), max_digits=12, decimal_places=0)
    discount = models.DecimalField(_('Discount (Toman)'), max_digits=12, decimal_places=0, default=0)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='unpaid')
    issue_date = models.DateField(_('Issue date'), default=timezone.localdate)
    due_date = models.DateField(_('Due date'), null=True, blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    order = models.ForeignKey(
        'services.ServiceOrder', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices', verbose_name=_('Related order'),
    )
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, verbose_name=_('Issued by')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-issue_date', '-id']

    def clean(self):
        super().clean()
        errors = {}
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = _('Invoice amount must be greater than zero.')
        if self.discount is not None and self.discount < 0:
            errors['discount'] = _('Discount cannot be negative.')
        if self.amount is not None and self.discount is not None and self.discount > self.amount:
            errors['discount'] = _('Discount cannot exceed invoice amount.')
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
                        raise ValidationError({'invoice_number': _('The previous invoice number is invalid.')})
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
        ('cash', _('Cash')),
        ('card', _('Card transfer')),
        ('online', _('Online gateway')),
        ('transfer', _('Bank transfer')),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name=_('Invoice')
    )
    amount = models.DecimalField(_('Amount (Toman)'), max_digits=12, decimal_places=0)
    method = models.CharField(_('Payment method'), max_length=10, choices=METHOD_CHOICES, default='cash')
    paid_at = models.DateTimeField(_('Paid at'), default=timezone.now)
    reference = models.CharField(_('Reference number'), max_length=100, blank=True)
    recorded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, verbose_name=_('Recorded by')
    )

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-paid_at']

    def clean(self):
        super().clean()
        errors = {}
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = _('Payment amount must be greater than zero.')
        if self.invoice_id and self.amount is not None:
            invoice = self.invoice
            paid = invoice.payments.exclude(pk=self.pk).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            if invoice.status == 'cancelled':
                errors['invoice'] = _('Payments cannot be recorded for a cancelled invoice.')
            elif self.amount > invoice.total - paid:
                errors['amount'] = _('Payment amount exceeds the outstanding invoice balance.')
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
