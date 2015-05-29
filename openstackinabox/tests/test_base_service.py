import unittest

from openstackinabox.services.base_service import BaseService


class TestBaseService(unittest.TestCase):

    def setUp(self):
        super(TestBaseService, self).setUp()

    def tearDown(self):
        super(TestBaseService, self).tearDown()

    def test_instantiation(self):
        bs = BaseService('instantiationTest')

        self.assertTrue(bs.is_base)

        with self.assertRaises(NotImplementedError):
            bs.get_model()

        x = []
        with self.assertRaises(NotImplementedError):
            bs.set_model(x)
