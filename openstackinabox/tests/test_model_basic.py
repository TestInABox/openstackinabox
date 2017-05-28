"""
Stack-In-A-Box: Basic Test
"""
import json
import unittest

import httpretty
import mock
import requests
import stackinabox.util_httpretty
from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


@httpretty.activate
class TestKeystoneModel(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneModel, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }

    def tearDown(self):
        super(TestKeystoneModel, self).tearDown()
        StackInABox.reset_services()

    def test_keystone_set_model(self):
        with self.assertRaises(TypeError):
            self.keystone.model = None

        self.keystone.model = KeystoneModel()

    def test_get_tenant_details(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        tenant_details = self.keystone.model.get_admin_tenant_details
        self.assertEqual(tenant_details['name'], 'system')
        self.assertEqual(tenant_details['description'], 'system administrator')

    def test_get_user_details(self):
        user_details = self.keystone.model.get_admin_user_details
        self.assertEqual(user_details['username'], 'system')
        self.assertEqual(user_details['email'], 'system@stackinabox')
        self.assertEqual(user_details['password'], 'stackinabox')
        self.assertEqual(user_details['apikey'], '537461636b496e41426f78')
