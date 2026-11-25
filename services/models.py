from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ServicePlan(models.Model):
    """A sellable service plan: internet, hosting/domain/server, software license."""

    CATEGORY_CHOICES = [
        ('internet', _('Internet (ADSL/TD-LTE)')),
        ('hosting', _('Hosting/Domain/Server')),
        ('license', _('Software License')),
    ]
    DURATION_CHOICES = [
        (1, _('Monthly')),
        (3, _('Quarterly')),
        (6, _('Semi-annual')),
        (12, _('Annual')),
    ]

    name = models.CharField(_('Plan name'), max_length=120)
    category = models.CharField(_('Category'), max_length=20, choices=CATEGORY_CHOICES)
    duration_months = models.PositiveIntegerField(
        _('Duration (months)'), choices=DURATION_CHOICES, default=1
    )
    price = models.DecimalField(_('Price (Toman)'), max_digits=12, decimal_places=0)
    specs = models.TextField(
        _('Specifications'), blank=True,
        help_text=_('e.g. 8Mbps, 100GB SSD, license version'),
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Service plan')
        verbose_name_plural = _('Service plans')
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_duration_months_display()})'


class Customer(models.Model):
    """Customer information entered by admin/staff."""

    full_name = models.CharField(_('Full name'), max_length=150)
    phone = models.CharField(_('Phone'), max_length=15)
    email = models.EmailField(_('Email'), blank=True)
    national_code = models.CharField(_('National ID'), max_length=10, blank=True)
    company = models.CharField(_('Company'), max_length=150, blank=True)
    address = models.TextField(_('Address'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class ServiceOrder(models.Model):
    """A customer's service subscription."""

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('cancelled', _('Cancelled')),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='orders', verbose_name=_('Customer')
    )
    plan = models.ForeignKey(
        ServicePlan, on_delete=models.PROTECT, related_name='orders', verbose_name=_('Plan')
    )
    start_date = models.DateField(_('Start date'), default=timezone.localdate)
    end_date = models.DateField(_('End date'))
    status = models.CharField(_('Status'), max_length=12, choices=STATUS_CHOICES, default='active')
    account_info = models.CharField(
        _('Account info / username'), max_length=200, blank=True,
        help_text=_('e.g. ADSL username or registered domain'),
    )
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Service order')
        verbose_name_plural = _('Service orders')
        ordering = ['-end_date']

    def save(self, *args, **kwargs):
        if not self.end_date and self.start_date and self.plan_id:
            self.end_date = self.start_date + timedelta(days=30 * self.plan.duration_months)
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        if self.status != 'active':
            return None
        return (self.end_date - timezone.localdate()).days

    @property
    def is_expiring_soon(self):
        days = self.days_remaining
        return days is not None and days <= 14

    def __str__(self):
        return f'{self.customer} — {self.plan.name}'
