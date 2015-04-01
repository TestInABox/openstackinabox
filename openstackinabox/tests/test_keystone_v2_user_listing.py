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
class TestKeystoneV2UserListing(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserListing, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserListing, self).tearDown()
        StackInABox.reset_services()

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

    def test_user_listing_by_name(self):
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

        res = requests.get('http://localhost/keystone/v2.0/users?name=tom',
                           headers=self.headers)
        self.assertEqual(res.status_code, 200)
        user_data = res.json()

        self.assertIn('user', user_data)
        self.assertEqual(len(user_data), 1)
        self.assertEqual(user_data['user']['username'], 'tom')

    def test_user_listing_with_invalid_query_param(self):
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
        res = requests.get('http://localhost/keystone/v2.0/users'
                           '?honesty=False',
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
