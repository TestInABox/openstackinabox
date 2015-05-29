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


class TestKeystoneV2Tenants(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2Tenants, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2Tenants, self).tearDown()
        StackInABox.reset_services()

    def test_tenant_listing_no_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            res = requests.get('http://localhost/keystone/v2.0/tenants')
            self.assertEqual(res.status_code, 403)

    def test_tenant_listing_invalid_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            self.headers['x-auth-token'] = 'new_token'
            res = requests.get('http://localhost/keystone/v2.0/tenants',
                               headers=self.headers)
            self.assertEqual(res.status_code, 401)

    def test_tenant_listing(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            res = requests.get('http://localhost/keystone/v2.0/tenants',
                               headers=self.headers)
            self.assertEqual(res.status_code, 200)
            tenant_data = res.json()

            # There is always 1 tenant - the system
            self.assertEqual(len(tenant_data['tenants']), 1)

            self.keystone.model.add_tenant(tenantname='neo',
                                           description='The One')

            res = requests.get('http://localhost/keystone/v2.0/tenants',
                               headers=self.headers)
            self.assertEqual(res.status_code, 200)
            tenant_data = res.json()

            self.assertEqual(len(tenant_data['tenants']), 2)
            self.assertEqual(tenant_data['tenants'][1]['name'], 'neo')
            self.assertEqual(tenant_data['tenants'][1]['description'],
                             'The One')
            self.assertTrue(tenant_data['tenants'][1]['enabled'])
