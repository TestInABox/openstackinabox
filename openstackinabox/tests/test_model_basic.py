"""
Stack-In-A-Box: Basic Test
"""
import json
import unittest

import mock
import requests
import stackinabox.util_requests_mock

from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneModel(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneModel, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        self.session = requests.Session()

    def tearDown(self):
        super(TestKeystoneModel, self).tearDown()
        StackInABox.reset_services()
        self.session.close()

    def test_keystone_set_model(self):
        with self.assertRaises(TypeError):
            self.keystone.model = None

        self.keystone.model = KeystoneModel()

    def test_get_tenant_details(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            tenant_details = self.keystone.model.get_admin_tenant_details
            self.assertEqual(tenant_details['name'], 'system')
            self.assertEqual(tenant_details['description'], 
                'system administrator')

    def test_get_user_details(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            user_details = self.keystone.model.get_admin_user_details
            self.assertEqual(user_details['username'], 'system')
            self.assertEqual(user_details['email'], 'system@stackinabox')
            self.assertEqual(user_details['password'], 'stackinabox')
            self.assertEqual(user_details['apikey'], '537461636b496e41426f78')
