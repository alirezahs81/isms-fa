# سیستم مدیریت خدمات اینترنتی (ISMS)

سیستم مدیریت فروش و اشتراک سرویس‌های اینترنتی — نسخه فارسی با رابط کاربری راست‌چین (RTL).

## امکانات

- **داشبورد:** آمار کلی، یادآور تمدید سرویس‌های نزدیک به انقضا (۱۴ روز آینده) و فاکتورهای پرداخت‌نشده
- **مدیریت مشتریان:** ثبت، ویرایش، جست‌وجو و مشاهده پروفایل مشتری همراه سرویس‌ها و فاکتورها
- **پلن‌های سرویس:** اینترنت (ADSL/TD-LTE)، هاست/دامنه/سرور و لایسنس نرم‌افزار
- **مدیریت سرویس‌ها:** ثبت سرویس، فیلتر وضعیت، تمدید و صدور فاکتور تمدید
- **فاکتور و پرداخت:** شماره‌گذاری خودکار، تخفیف، ثبت پرداخت و ابطال فاکتور
- **گزارش‌ها و کاربران:** گزارش درآمد و مطالبات، مدیریت کاربران ادمین/کارمند
- **پنل Django Admin:** مدیریت داده‌ها در `/admin/`

دسترسی بخش‌های مدیریتی به کاربران مجاز ادمین/کارمند محدود شده است.

## فناوری‌ها و نسخه‌های مورد استفاده

- Python **3.12** در CI
- Django با بازه وابستگی تعریف‌شده در `requirements.txt`: `>=5.0,<7`
- PostgreSQL **16** در CI
- HTML/CSS

نسخه Django در حال حاضر به یک نسخه جزئی مشخص pin نشده است؛ نصب وابستگی‌ها نسخه سازگار را از بازه بالا انتخاب می‌کند. بنابراین نسخه دقیق نصب‌شده ممکن است با زمان تغییر کند.

## پیش‌نیازها

- Python 3.12
- PostgreSQL 16 (یا نسخه سازگار PostgreSQL)
- Git (اختیاری، برای دریافت مخزن)

## راه‌اندازی در Windows PowerShell

دستورهای زیر را در پوشه اصلی پروژه اجرا کنید.

### ۱. ساخت محیط مجازی و نصب وابستگی‌ها

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

اگر PowerShell اجرای اسکریپت فعال‌سازی را مسدود کرد، می‌توانید بدون تغییر Execution Policy از مسیر مستقیم Python استفاده کنید:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### ۲. ساخت دیتابیس

در صورت نصب بودن ابزارهای PostgreSQL، دستور زیر را اجرا کنید:

```powershell
psql -U postgres -c "CREATE DATABASE isms;"
```

اگر دیتابیس از قبل وجود دارد، این مرحله را رد کنید.

### ۳. تنظیم متغیرهای محیطی برای محیط توسعه

در PowerShell:

```powershell
$env:ISMS_DB_NAME = "isms"
$env:ISMS_DB_USER = "postgres"
$env:ISMS_DB_PASSWORD = "رمز_کاربر_پایگاه_داده"
$env:ISMS_DB_HOST = "127.0.0.1"
$env:ISMS_DB_PORT = "5432"
$env:ISMS_DEBUG = "1"
$env:ISMS_SECRET_KEY = (python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
```

این متغیرها فقط تا پایان همان نشست PowerShell معتبر هستند. برای اجرای مجدد پروژه در یک نشست جدید، آن‌ها را دوباره تنظیم کنید.

در حالت توسعه، `ISMS_DEBUG=1` اجازه استفاده از کلید توسعه داخلی را می‌دهد؛ با این حال، ساخت و استفاده از کلید تصادفی بالا توصیه می‌شود. در حالت پیش‌فرض امن (`ISMS_DEBUG=0`)، تنظیم `ISMS_SECRET_KEY` الزامی است و برنامه بدون آن اجرا نمی‌شود.

### ۴. اجرای Migration، ساخت مدیر و اجرای سرور

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

سپس به نشانی `http://127.0.0.1:8000` بروید.

## متغیرهای محیطی

| متغیر | پیش‌فرض در کد | توضیح |
|---|---|---|
| `ISMS_DB_NAME` | `isms` | نام دیتابیس |
| `ISMS_DB_USER` | `postgres` | کاربر دیتابیس |
| `ISMS_DB_PASSWORD` | `postgres` | رمز دیتابیس؛ در محیط واقعی حتماً تغییر دهید |
| `ISMS_DB_HOST` | `127.0.0.1` | میزبان دیتابیس |
| `ISMS_DB_PORT` | `5432` | پورت دیتابیس |
| `ISMS_DEBUG` | `0` | فقط مقدار `1` حالت Debug را فعال می‌کند |
| `ISMS_SECRET_KEY` | بدون مقدار | در حالت غیردیباگ الزامی است |
| `ISMS_ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver` | فهرست میزبان‌های مجاز، جداشده با کاما |
| `ISMS_CSRF_TRUSTED_ORIGINS` | خالی | مبدأهای مورد اعتماد CSRF، جداشده با کاما و همراه scheme مانند `https://example.com` |
| `ISMS_SECURE_SSL_REDIRECT` | `1` در حالت غیردیباگ | تغییر مسیر HTTP به HTTPS |
| `ISMS_HSTS_SECONDS` | `31536000` در حالت غیردیباگ | مدت HSTS بر حسب ثانیه |

## تنظیمات محیط عملیاتی

- `ISMS_DEBUG=0` را تنظیم کنید و یک `ISMS_SECRET_KEY` تصادفی و محرمانه در secret manager یا محیط اجرا قرار دهید.
- `ISMS_ALLOWED_HOSTS` و در صورت نیاز `ISMS_CSRF_TRUSTED_ORIGINS` را متناسب با دامنه واقعی تنظیم کنید.
- رمز دیتابیس پیش‌فرض را تغییر دهید.
- چون SSL redirect و HSTS در حالت غیردیباگ به‌صورت پیش‌فرض فعال‌اند، فقط پشت HTTPS معتبر از برنامه استفاده کنید و تنظیمات reverse proxy را مطابق استقرار خود انجام دهید.
- مقادیر محرمانه را در مخزن Git commit نکنید.

## بررسی خودکار (CI)

GitHub Actions با Python 3.12 و PostgreSQL 16 این مراحل را اجرا می‌کند:
1. نصب وابستگی‌ها
2. بررسی نبود تغییر مدلِ بدون migration با `python manage.py makemigrations --check --dry-run`
3. اجرای migrationها
4. اجرای `python manage.py check`
5. اجرای تست‌ها

سبز بودن CI به معنی انجام آزمون استقرار روی زیرساخت عملیاتی واقعی نیست.

## ساختار پروژه

```
isms/
├── services/     # مشتریان، پلن‌های سرویس و سفارش‌ها
├── invoices/     # فاکتورها و پرداخت‌ها
├── accounts/     # مدیریت کاربران
├── dashboard/    # داشبورد و گزارش‌ها
├── templates/    # قالب‌های فارسی RTL
└── isms/         # تنظیمات پروژه
```

## لایسنس

MIT
