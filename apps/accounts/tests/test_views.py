from unittest import mock

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from waffle.testutils import override_switch

from accounts.models import MoodyUser, UserProfile
from libs.tests.helpers import MoodyUtil, get_messages_from_response


class TestLoginView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:login')
        cls.user = MoodyUtil.create_user(create_user_profile=True)

    def test_login_redirects_to_valid_path(self):
        next = reverse('moodytunes:browse')
        url = self.url + '?next={}'.format(next)

        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(url, data=data)

        self.assertRedirects(resp, next)

    @override_switch('show_spotify_auth_prompt', active=True)
    def test_login_redirect_to_default(self):
        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth=True')

    @override_switch('show_spotify_auth_prompt', active=False)
    def test_get_login_page_for_authenticated_user_redirects_to_default(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        resp = self.client.get(self.url)

        self.assertRedirects(resp, f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth=False')

    def test_login_returns_bad_request_for_invalid_redirect_url(self):
        next = '6330599317423175408.owasp.org'
        url = self.url + '?next={}'.format(next)

        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_switch('show_spotify_auth_prompt', active=True)
    def test_context_sets_show_spotify_auth_to_false_for_existing_auth_record(self):
        MoodyUtil.create_spotify_user_auth(self.user)

        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth=False')

        # Ensure UserProfile record is updated to indicate user has already authenticated with Spotify
        self.user.userprofile.refresh_from_db()
        self.assertTrue(self.user.userprofile.has_rejected_spotify_auth)

    @override_switch('show_spotify_auth_prompt', active=True)
    def test_context_sets_show_spotify_auth_to_true_for_missing_auth_record(self):
        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth=True')

    @override_switch('show_spotify_auth_prompt', active=True)
    def test_context_sets_show_spotify_auth_to_false_for_rejected_spotify_auth(self):
        self.user.userprofile.has_rejected_spotify_auth = True
        self.user.userprofile.save()

        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth=False')

    @override_switch('show_spotify_auth_prompt', active=False)
    def test_context_sets_show_spotify_auth_to_false_when_switch_is_not_active(self):
        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth=False')

    @mock.patch('accounts.utils.logger')
    def test_failed_login_calls_log_failed_login(self, mock_failed_login_logger):
        ip_address = '192.168.0.201'

        data = {
            'username': self.user.username,
            'password': 'wrong-password'
        }

        self.client.post(self.url, data=data, HTTP_X_FORWARDED_FOR=ip_address)

        mock_failed_login_logger.warning.assert_called_once_with(
            'Failed login attempt for {}'.format(self.user.username),
            extra={
                'fingerprint': 'accounts.utils.log_failed_login_attempt',
                'username': self.user.username,
                'ip_address': ip_address,
                'application_host': 'www',
            }
        )


class TestLogoutView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.app_url = 'https://moodytuns.vm/accounts/logout/'
        cls.admin_url = 'https://admin.moodytunes.vm/logout/'

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_logout_from_app_site_redirects_to_app_login_page(self):
        resp = self.client.get(self.app_url, follow=True)
        self.assertIn('login.html', resp.template_name)

    @override_settings(DEFAULT_HOST='admin')
    def test_logout_from_admin_site_redirects_to_admin_login_page(self):
        resp = self.client.get(self.admin_url, follow=True)
        self.assertIn('admin/login.html', resp.template_name)


class TestProfileView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:profile')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_redirect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, expected_redirect)


class TestUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:update')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_redirect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, expected_redirect)

    def test_get_request_populates_form_with_initial_user_data(self):
        user = MoodyUtil.create_user(email='foo@example.com')
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Ensure that the form's initial data is set to the current data for the user
        self.assertEqual(resp.context['form'].initial['username'], user.username)
        self.assertEqual(resp.context['form'].initial['email'], user.email)

    def test_happy_path(self):
        user = MoodyUtil.create_user()
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        update_data = {
            'username': 'my_new_user',
            'email': 'foo@example.com',
        }

        resp = self.client.post(self.url, data=update_data, follow=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(user.username, update_data['username'])
        self.assertEqual(user.email, update_data['email'])

    def test_updating_user_with_existing_username_is_rejected(self):
        user = MoodyUtil.create_user()
        other_user = MoodyUtil.create_user(username='something_else')
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        request_data = {'username': other_user.username}

        resp = self.client.post(self.url, data=request_data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(MoodyUser.objects.filter(username=user.username).count(), 1)
        self.assertEqual(MoodyUser.objects.filter(username=other_user.username).count(), 1)
        self.assertIn(b'This username is already taken. Please choose a different one', resp.content)

    def test_updating_user_with_invalid_username_is_rejected(self):
        user = MoodyUtil.create_user()
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        request_data = {
            'username': 'zap" AND "1"="1" --',
        }

        old_username = user.username

        resp = self.client.post(self.url, data=request_data)

        user.refresh_from_db()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(user.username, old_username)  # Ensure user username was not updated to bad value
        self.assertIn(
            b'Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.',
            resp.content
        )

    def test_updating_user_with_empty_email_deletes_email_value_from_record(self):
        user = MoodyUtil.create_user(email='foo@example.com')
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        request_data = {
            'username': user.username,
            'email': ''
        }

        resp = self.client.post(self.url, data=request_data, follow=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(user.email, '')


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

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, reverse('accounts:login'))
        self.assertTrue(MoodyUser.objects.filter(username=user_data['username']).exists())
        self.assertTrue(UserProfile.objects.filter(user__username=user_data['username']).exists())

        # Ensure user can login with their new account
        request = mock.Mock()
        request.host.name = 'www'
        user = authenticate(request, username=user_data['username'], password=user_data['password'])
        self.assertIsNotNone(user, 'User was not successfully created! Could not authenticate with new user.')

    def test_creating_user_with_existing_username_is_rejected(self):
        user = MoodyUtil.create_user()
        request_data = {
            'username': user.username,
            'password': 'superSecret123',
            'confirm_password': 'superSecret123'
        }

        resp = self.client.post(self.url, data=request_data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(MoodyUser.objects.filter(username=user.username).count(), 1)
        self.assertIn(b'This username is already taken. Please choose a different one', resp.content)

    def test_creating_user_with_invalid_username_is_rejected(self):
        request_data = {
            'username': 'zap" AND "1"="1" --',
            'password': 'superSecret123',
            'confirm_password': 'superSecret123'
        }

        resp = self.client.post(self.url, data=request_data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(MoodyUser.objects.filter(username=request_data['username']).exists())
        self.assertIn(
            b'Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.',
            resp.content
        )


class TestMoodyPasswordResetView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:reset-password')
        cls.user = MoodyUtil.create_user(email='foo@example.com')

    @mock.patch('django.contrib.auth.tokens.PasswordResetTokenGenerator.make_token')
    @mock.patch('django.contrib.auth.forms.PasswordResetForm.send_mail')
    def test_happy_path(self, mock_send_mail, mock_token_generator):
        mock_token_generator.return_value = 'foo-bar'
        expected_redirect = reverse('accounts:login')
        data = {'email': self.user.email}

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, expected_redirect)

        messages = get_messages_from_response(resp)
        self.assertIn('We have sent a password reset email to the address provided', messages)

        email_context = {
            'email': 'foo@example.com',
            'domain': 'testserver',
            'site_name': 'testserver',
            'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
            'user': self.user,
            'token': mock_token_generator(),
            'protocol': 'http'
        }

        mock_send_mail.assert_called_once_with(
            'registration/password_reset_subject.txt',
            'password_reset_email.html',
            email_context,
            None,  # From email, defaults to DEFAULT_FROM_EMAIL
            self.user.email,
            html_email_template_name=None
        )

    @mock.patch('django.contrib.auth.forms.PasswordResetForm.send_mail')
    def test_bad_email_is_rejected(self, mock_send_mail):
        data = {'email': 'bad-data'}

        resp = self.client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('Enter a valid email address.', resp.context['form'].errors['email'])

        mock_send_mail.assert_not_called()


class TestMoodyPasswordResetConfirmView(TestCase):
    def test_happy_path(self):
        user = MoodyUtil.create_user(email='foo@example.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        url = reverse('accounts:password-reset-confirm', kwargs={'uidb64': uid, 'token': token})

        initial_resp = self.client.get(url)
        reset_url = initial_resp['Location']

        expected_redirect = reverse('accounts:password-reset-complete')
        data = {
            'new_password1': 'password',
            'new_password2': 'password'
        }

        resp = self.client.post(reset_url, data=data)

        self.assertRedirects(resp, expected_redirect, fetch_redirect_response=False)

        # Test password updated OK
        user.refresh_from_db()
        updated_user = authenticate(username=user.username, password=data['new_password1'])

        self.assertEqual(user.pk, updated_user.pk)

    def test_non_matching_passwords_are_rejected(self):
        user = MoodyUtil.create_user(email='foo@example.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        url = reverse('accounts:password-reset-confirm', kwargs={'uidb64': uid, 'token': token})

        initial_resp = self.client.get(url)
        reset_url = initial_resp['Location']

        data = {
            'new_password1': 'foo',
            'new_password2': 'bar'
        }

        resp = self.client.post(reset_url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("The two password fields didn't match.", resp.context['form'].errors['new_password2'])


class TestMoodyPasswordResetDone(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:password-reset-complete')

    def test_happy_path(self):
        expected_redirect = reverse('accounts:login')
        resp = self.client.get(self.url)

        self.assertRedirects(resp, expected_redirect)

        messages = get_messages_from_response(resp)
        self.assertIn('Please login with your new password', messages)


class TestUserProfileView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_profile = MoodyUtil.create_user()
        cls.user_without_profile = MoodyUtil.create_user(username='test-no-profile')
        cls.url = reverse('accounts:user-profile')

        cls.user_profile = MoodyUtil.create_user_profile(cls.user_with_profile, has_rejected_spotify_auth=False)

    def setUp(self):
        self.client.login(username=self.user_with_profile.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_get_request_is_rejected(self):
        self.client.logout()

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_update_request_is_rejected(self):
        self.client.logout()

        resp = self.client.patch(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_request_returns_user_profile(self):
        resp = self.client.get(self.url)
        resp_json = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_json['user_id'], self.user_with_profile.pk)
        self.assertFalse(resp_json['has_rejected_spotify_auth'])

    def test_get_request_for_user_with_no_user_profile_returns_not_found(self):
        self.client.logout()
        self.client.login(username=self.user_without_profile.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_request_updates_user_profile_attributes(self):
        data = {'has_rejected_spotify_auth': True}

        resp = self.client.patch(self.url, data)
        self.user_profile.refresh_from_db()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user_profile.has_rejected_spotify_auth)

    def test_update_request_with_no_data_does_not_update_user_profile_attributes(self):
        data = {}

        resp = self.client.patch(self.url, data)
        self.user_profile.refresh_from_db()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user_profile.has_rejected_spotify_auth)

    def test_update_request_with_invalid_parameters_returns_bad_request(self):
        data = {'has_rejected_spotify_auth': 'foo'}

        resp = self.client.patch(self.url, data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_request_for_user_with_no_user_profile_returns_not_found(self):
        self.client.logout()
        self.client.login(username=self.user_without_profile.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        data = {'has_rejected_spotify_auth': True}

        resp = self.client.patch(self.url, data)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
