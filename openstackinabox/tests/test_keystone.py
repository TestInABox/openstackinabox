"""
Stack-In-A-Box: Basic Test
"""
import unittest

import httpretty
import requests
import stackinabox.util_httpretty
from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


@httpretty.activate
class TestHttprettyKeystone(unittest.TestCase):

    def setUp(self):
        super(TestHttprettyKeystone, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestHttprettyKeystone, self).tearDown()
        StackInABox.reset_services()

    def test_keystone_set_model(self):
        with self.assertRaises(TypeError):
            self.keystone.model = None

        self.keystone.model = KeystoneModel()

    def test_tenant_listing_no_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')

        res = requests.get('http://localhost/keystone/v2.0/tenants')
        self.assertEqual(res.status_code, 403)

    def test_tenant_listing_invalid_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')

        self.headers['x-auth-token'] = 'new_token'
        res = requests.get('http://localhost/keystone/v2.0/tenants',
                           headers=self.headers)
        self.assertEqual(res.status_code, 401)

    def test_tenant_listing(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')

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
        self.assertEqual(tenant_data['tenants'][1]['description'], 'The One')
        self.assertTrue(tenant_data['tenants'][1]['enabled'])

    def test_user_listing_no_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        
        res = requests.get('http://localhost/keystone/v2.0/users')
        self.assertEqual(res.status_code, 403)

    def test_user_listing_bad_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        
        self.headers['x-auth-token'] = 'new_token'
        res = requests.get('http://localhost/keystone/v2.0/users',
                           headers=self.headers)
        self.assertEqual(res.status_code, 401)

    def test_user_listing(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        
        neo_tenant_id = self.keystone.model.add_tenant(tenantname='neo',
                                                         description='The One')
        tom = self.keystone.model.add_user(neo_tenant_id,
                                           'tom',
                                           'tom@theone.matrix',
                                           'bluepill',
                                           'iamnottheone',
                                           enabled=True)

        self.keystone.model.add_user_role_by_rolename(neo_tenant_id,
                                                      tom,
                                                      'identity:user-admin')
        self.keystone.model.add_token(neo_tenant_id, tom)
        user_data = self.keystone.model.get_token_by_userid(tom)

        self.headers['x-auth-token'] = user_data['token']
        res = requests.get('http://localhost/keystone/v2.0/users',
                           headers=self.headers)
        self.assertEqual(res.status_code, 200)
        user_data = res.json()

        self.assertEqual(len(user_data['users']), 1)

        self.keystone.model.add_user(neo_tenant_id,
                                       'neo',
                                       'neo@theone.matrix',
                                       'redpill',
                                       'iamtheone',
                                       enabled=True)

        res = requests.get('http://localhost/keystone/v2.0/users',
                           headers=self.headers)
        self.assertEqual(res.status_code, 200)
        user_data = res.json()

        self.assertEqual(len(user_data['users']), 2)
