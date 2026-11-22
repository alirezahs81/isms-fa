from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('', include('services.urls')),
    path('', include('invoices.urls')),
    path('accounts/', include('accounts.urls')),
]
