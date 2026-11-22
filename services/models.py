from django.db import models
from django.utils import timezone
from datetime import timedelta


class ServicePlan(models.Model):
    """پلن سرویس قابل فروش: اینترنت، هاست/دامنه/سرور، لایسنس نرم‌افزار"""
    CATEGORY_CHOICES = [
        ('internet', 'اینترنت (ADSL/TD-LTE)'),
        ('hosting', 'هاست/دامنه/سرور'),
        ('license', 'لایسنس نرم‌افزار'),
    ]
    DURATION_CHOICES = [
        (1, 'ماهانه'),
        (3, 'سه‌ماهه'),
        (6, 'شش‌ماهه'),
        (12, 'سالانه'),
    ]

    name = models.CharField('نام پلن', max_length=120)
    category = models.CharField('دسته‌بندی', max_length=20, choices=CATEGORY_CHOICES)
    duration_months = models.PositiveIntegerField('مدت (ماه)', choices=DURATION_CHOICES, default=1)
    price = models.DecimalField('قیمت (تومان)', max_digits=12, decimal_places=0)
    specs = models.TextField('مشخصات', blank=True, help_text='مثلاً: 8Mbps، 100GB SSD، نسخه لایسنس')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'پلن سرویس'
        verbose_name_plural = 'پلن‌های سرویس'
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_duration_months_display()})'


class Customer(models.Model):
    """مشتری (اطلاعات توسط ادمین/کارمند ثبت می‌شود)"""
    full_name = models.CharField('نام و نام خانوادگی', max_length=150)
    phone = models.CharField('موبایل', max_length=15)
    email = models.EmailField('ایمیل', blank=True)
    national_code = models.CharField('کد ملی', max_length=10, blank=True)
    company = models.CharField('شرکت/سازمان', max_length=150, blank=True)
    address = models.TextField('آدرس', blank=True)
    notes = models.TextField('یادداشت', blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'مشتری'
        verbose_name_plural = 'مشتریان'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class ServiceOrder(models.Model):
    """سرویس فعال یک مشتری (اشتراک خریداری‌شده)"""
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('expired', 'منقضی'),
        ('cancelled', 'لغو شده'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders', verbose_name='مشتری')
    plan = models.ForeignKey(ServicePlan, on_delete=models.PROTECT, related_name='orders', verbose_name='پلن')
    start_date = models.DateField('تاریخ شروع', default=timezone.localdate)
    end_date = models.DateField('تاریخ پایان')
    status = models.CharField('وضعیت', max_length=12, choices=STATUS_CHOICES, default='active')
    account_info = models.CharField('اطلاعات حساب/نام کاربری', max_length=200, blank=True,
                                    help_text='مثلاً: نام کاربری ADSL یا دامنه ثبت‌شده')
    notes = models.TextField('یادداشت', blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'سفارش سرویس'
        verbose_name_plural = 'سفارش‌های سرویس'
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
        d = self.days_remaining
        return d is not None and d <= 14

    def __str__(self):
        return f'{self.customer} — {self.plan.name}'
