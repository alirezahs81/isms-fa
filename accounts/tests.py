from django.test import TestCase

# Create your tests here.


from .views import UserForm


class StaffPasswordValidationTests(TestCase):
    def test_common_password_is_rejected(self):
        form = UserForm(data={'username': 'weak-password-user', 'password': 'password', 'is_staff': True})
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_short_password_is_rejected(self):
        form = UserForm(data={'username': 'short-password-user', 'password': '123', 'is_staff': True})
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
