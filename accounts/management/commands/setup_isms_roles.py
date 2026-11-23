from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


ROLE_GROUPS = {
    "isms_admin": "Full application access (assign only to trusted staff)",
    "isms_finance": "Invoices, payments, customer and service read access",
    "isms_support": "Customer and service operations; no financial records",
    "isms_viewer": "Reserved read-only role; no access to customer-sensitive or financial screens",
}


class Command(BaseCommand):
    help = "Create the standard ISMS role groups."

    def handle(self, *args, **options):
        for name, description in ROLE_GROUPS.items():
            group, created = Group.objects.get_or_create(name=name)
            self.stdout.write(
                self.style.SUCCESS(f'Created {name}') if created else f'Exists: {name}'
            )
