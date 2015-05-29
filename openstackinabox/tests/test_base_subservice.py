import unittest

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.base_subservice import BaseSubService


class ServiceExample(BaseService):

    def __init__(self, name):
        super(ServiceExample, self).__init__(name)
        self.__model = {}

    def get_model(self):
        return self.__model

    def set_model(self, value):
        self.__model = value


class TestBaseSubService(unittest.TestCase):

    def setUp(self):
        super(TestBaseSubService, self).setUp()

    def tearDown(self):
        super(TestBaseSubService, self).tearDown()

    def test_instantiation(self):
        bs = ServiceExample('service')
        bss = BaseSubService('subService', bs)
        self.assertFalse(bss.is_base)

        bss_parent = bss.get_parent()
        self.assertEqual(bss_parent, bs)
