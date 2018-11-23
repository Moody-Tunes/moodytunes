from django.test import TestCase
from django.urls import reverse

from libs.tests.helpers import MoodyUtil


class TestHomePageView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('homepage')
        cls.user = MoodyUtil.create_user()

    def test_authenticated_user_redirect(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('accounts:profile'))

    def test_anonymous_user_redirect(self):
        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('accounts:login'))
