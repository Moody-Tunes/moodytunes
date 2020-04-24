from unittest import mock

from django.test import TestCase, override_settings

from base.templatetags.moody_tags import settings, user_agent_is_chrome


class TestSettingsTemplateTag(TestCase):
    @override_settings(TEST_SETTING='test-setting')
    def test_tag_returns_variable_if_found(self):
        ret = settings('TEST_SETTING')
        self.assertEqual(ret, 'test-setting')

    @override_settings(TEST_SETTING='test-setting')
    def test_tag_works_with_lowercase_settings_name(self):
        ret = settings('test_setting')
        self.assertEqual(ret, 'test-setting')

    def test_tag_returns_empty_string_if_variable_not_found(self):
        ret = settings('TEST_SETTING')
        self.assertEqual(ret, '')


class TestUserAgentIsChromeTemplateTag(TestCase):
    def test_tag_returns_true_for_chrome_user_agent(self):
        request = mock.Mock()
        request.user_agent.browser.family = 'Chrome'
        self.assertTrue(user_agent_is_chrome(request))

    def test_tag_returns_true_for_chromium_user_agent(self):
        request = mock.Mock()
        request.user_agent.browser.family = 'Chromium'
        self.assertTrue(user_agent_is_chrome(request))

    def test_tag_returns_false_for_firefox_user_agent(self):
        request = mock.Mock()
        request.user_agent.browser.family = 'Firefox'
        self.assertFalse(user_agent_is_chrome(request))
