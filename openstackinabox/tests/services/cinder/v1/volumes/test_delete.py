"""
"""
import unittest

import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.cinder import CinderV1Service
from openstackinabox.services.keystone import KeystoneV2Service


class TestCinderV1Delete(unittest.TestCase):

    def setUp(self):
        super(TestCinderV1Delete, self).setUp()
        self.keystone = KeystoneV2Service()
        self.cinder = CinderV1Service(self.keystone)
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
        }
        StackInABox.register_service(self.keystone)
        StackInABox.register_service(self.cinder)

    def tearDown(self):
        super(TestCinderV1Delete, self).tearDown()
        StackInABox.reset_services()

    def test_volume_delete(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            res = requests.delete(
                'http://localhost/cinder/v1/volumes/example'
            )
            self.assertEqual(res.status_code, 500)
