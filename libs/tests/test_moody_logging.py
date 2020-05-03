from django.test import TestCase

from libs.moody_logging import auto_fingerprint


class Test(object):
    def foo(self):
        return None


class TestAutoFingerprint(TestCase):
    def test_happy_path(self):
        test = Test()
        fingerprint = auto_fingerprint(test, test.foo.__name__, 'testing')
        self.assertEqual(fingerprint, 'libs.tests.test_moody_logging.Test.foo.testing')
