from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardAccessTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_regular_user_cannot_view_dashboard_or_reports(self):
        user = get_user_model().objects.create_user(username='regular-dashboard-test', password='Strong-Test-Password-928!')
        self.client.force_login(user)
        for url in (reverse('dashboard:home'), reverse('dashboard:reports')):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_staff_user_can_view_dashboard_and_reports(self):
        user = get_user_model().objects.create_user(username='staff-dashboard-test', password='Strong-Test-Password-928!', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:reports')).status_code, 200)
