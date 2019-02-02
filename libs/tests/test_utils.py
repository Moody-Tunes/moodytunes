from django.test import TestCase

from libs.utils import average


class TestAverage(TestCase):
    def test_happy_path(self):
        collection = [.5, .5]
        expected_average = .5

        calculated_average = average(collection)
        self.assertEqual(calculated_average, expected_average)

    def test_empty_list_returns_null(self):
        collection = []

        calculated_average = average(collection)
        self.assertIsNone(calculated_average)

    def test_non_number_passed_raises_value_error(self):
        collection = [0.5, 'Hello World!', 0.5]

        with self.assertRaises(ValueError):
            average(collection)
