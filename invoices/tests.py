from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class InvoiceMutationSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="invoice-staff-test", password="test-password", is_staff=True
        )
        self.client.force_login(self.staff)

    def test_invoice_cancel_rejects_get(self):
        response = self.client.get(reverse("invoices:cancel", args=[1]))
        self.assertEqual(response.status_code, 405)

    def test_invoice_from_order_rejects_get(self):
        response = self.client.get(reverse("invoices:from_order", args=[1]))
        self.assertEqual(response.status_code, 405)
