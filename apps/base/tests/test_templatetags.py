from django.test import TestCase, override_settings

from base.templatetags.moody_tags import settings


class TestSettingsTempateTag(TestCase):
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
