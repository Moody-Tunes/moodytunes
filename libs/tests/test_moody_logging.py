from django.test import TestCase

from libs.moody_logging import auto_fingerprint, update_logging_data


class Test(object):
    @update_logging_data
    def foo(self, **kwargs):
        return kwargs


class TestAutoFingerprint(TestCase):
    def test_happy_path(self):
        test = Test()
        kwargs = test.foo()
        fingerprint = auto_fingerprint('testing', **kwargs)

        self.assertEqual(fingerprint, 'libs.tests.test_moody_logging.Test.foo.testing')
