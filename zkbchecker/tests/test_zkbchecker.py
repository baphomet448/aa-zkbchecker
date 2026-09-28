"""
Example Test
"""

# Django
from django.test import TestCase


class TestZkbChecker(TestCase):
    """
    TestZkbChecker
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Test setup
        :return:
        :rtype:
        """

        super().setUpClass()

    def test_zkbchecker(self):
        """
        Dummy test function
        :return:
        :rtype:
        """

        self.assertEqual(True, True)
