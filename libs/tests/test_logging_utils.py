from django.conf import settings
from django.test import TestCase

from libs.moody_logging import format_module_name_with_project_prefix


class TestFormatModuleName(TestCase):

    def test_module_is_prefixed_with_project_name(self):
        name = 'my.module.path'
        module_name = format_module_name_with_project_prefix(name)

        self.assertTrue(module_name.startswith(settings.PROJECT_PREFIX))

    def test_module_in_apps_has_proper_path(self):
        name = 'base.validators'
        module_name = format_module_name_with_project_prefix(name)

        self.assertTrue(module_name.startswith(settings.PROJECT_PREFIX))
        self.assertTrue('apps' in module_name)

    def test_bad_module_path(self):
        name = 'this-dont-look-like-a-module'
        module_name = format_module_name_with_project_prefix(name)

        self.assertFalse(module_name)
