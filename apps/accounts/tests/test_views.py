from requests import codes

from django.test import TestCase
from django.urls import reverse

from accounts.models import MoodyUser
from libs.tests.helpers import MoodyUtil


class TestProfileView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:profile')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_rediect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, codes.found)
        self.assertRedirects(resp, expected_rediect)


class TestUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:update')
        cls.user = MoodyUtil.create_user()

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_rediect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, codes.found)
        self.assertRedirects(resp, expected_rediect)

    def test_happy_path(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        update_data = {
            'username': 'my_new_user',
            'email': 'foo@example.com',
            'password': '12345',
            'confirm_password': '12345'
        }

        resp = self.client.post(self.url, data=update_data, follow=True)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, update_data['username'])
        self.assertEqual(self.user.email, update_data['email'])

        self.assertEqual(resp.status_code, codes.okay)
        self.assertTemplateUsed(resp, 'login.html')


class TestCreateUserView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:create')

    def test_happy_path(self):
        user_data = {
            'username': 'new_user',
            'password': 'superSecret123',
            'confirm_password': 'superSecret123'
        }

        resp = self.client.post(self.url, data=user_data)

        self.assertEqual(resp.status_code, codes.found)
        self.assertRedirects(resp, reverse('accounts:login'))
        self.assertTrue(MoodyUser.objects.filter(username=user_data['username']).exists())
