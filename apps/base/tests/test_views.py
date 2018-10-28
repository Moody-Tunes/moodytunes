from django.test import TestCase
from django.urls import reverse

from accounts.models import MoodyUser


class TestHomePageView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('homepage')
        cls.password = 'foobar'

        cls.user = MoodyUser.objects.create(username='chester_mctester')
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_authenticated_user_redirect(self):
        self.client.login(username=self.user.username, password=self.password)

        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('accounts:profile'))

    def test_anonymous_user_reirect(self):
        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('accounts:login'))
