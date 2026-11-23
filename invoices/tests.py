from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from invoices.models import Invoice, Payment
from services.models import Customer, ServicePlan


class InvoiceMutationSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username="invoice-staff-test", password="test-password", is_staff=True)
        self.client.force_login(self.staff)

    def test_invoice_cancel_rejects_get(self):
        response = self.client.get(reverse("invoices:cancel", args=[1]))
        self.assertEqual(response.status_code, 405)

    def test_invoice_from_order_rejects_get(self):
        response = self.client.get(reverse("invoices:from_order", args=[1]))
        self.assertEqual(response.status_code, 405)


class FinancialValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="finance-test")
        self.customer = Customer.objects.create(full_name="Test Customer", phone="09120000000")
        self.plan = ServicePlan.objects.create(name="Test Plan", category="internet", price=Decimal("1000"))
        self.invoice = Invoice.objects.create(
            customer=self.customer, plan=self.plan, amount=Decimal("1000"),
            discount=Decimal("100"), created_by=self.user,
        )

    def test_invoice_rejects_non_positive_amount(self):
        invoice = Invoice(customer=self.customer, plan=self.plan, amount=Decimal("0"))
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_invoice_rejects_discount_above_amount(self):
        invoice = Invoice(customer=self.customer, plan=self.plan, amount=Decimal("100"), discount=Decimal("101"))
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_payment_rejects_zero_or_negative_amount(self):
        for amount in (Decimal("0"), Decimal("-1")):
            with self.subTest(amount=amount):
                payment = Payment(invoice=self.invoice, amount=amount, recorded_by=self.user)
                with self.assertRaises(ValidationError):
                    payment.full_clean()

    def test_payment_rejects_overpayment(self):
        payment = Payment(invoice=self.invoice, amount=Decimal("901"), recorded_by=self.user)
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_payment_cannot_be_recorded_for_cancelled_invoice(self):
        self.invoice.status = "cancelled"
        self.invoice.save()
        payment = Payment(invoice=self.invoice, amount=Decimal("1"), recorded_by=self.user)
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_valid_payment_marks_invoice_paid(self):
        Payment.objects.create(invoice=self.invoice, amount=Decimal("900"), recorded_by=self.user)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")
