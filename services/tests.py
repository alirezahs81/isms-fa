from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


class StaffMutationSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff-test", password="test-password", is_staff=True
        )
        self.staff.groups.add(Group.objects.create(name='isms_support'))
        self.client.force_login(self.staff)

    def test_service_renewal_rejects_get(self):
        response = self.client.get(reverse("order_renew", args=[1]))
        self.assertEqual(response.status_code, 405)


    def test_support_cannot_view_financial_records(self):
        response = self.client.get(reverse("invoices:list"))
        self.assertEqual(response.status_code, 403)

    def test_non_staff_cannot_create_customer(self):
        User = get_user_model()
        regular_user = User.objects.create_user(
            username="regular-test", password="test-password"
        )
        self.client.force_login(regular_user)
        response = self.client.get(reverse("customer_create"))
        self.assertEqual(response.status_code, 403)
