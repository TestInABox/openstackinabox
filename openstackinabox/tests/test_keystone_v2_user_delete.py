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
class TestKeystoneV2UserDelete(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserDelete, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        self.user_info = {
            'user': {
                'username': 'trinity',
                'enabled': True,
                'email': 'trinity@theone.matrix',
                'OS-KSADM:password': 'Inl0veWithNeo'
            }
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserDelete, self).tearDown()
        StackInABox.reset_services()

    def test_user_delete_no_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        res = requests.delete('http://localhost/keystone/v2.0/users/1234567890')
        self.assertEqual(res.status_code, 403)

    def test_user_delete_invalid_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        self.headers['x-auth-token'] = 'new_token'
        res = requests.delete('http://localhost/keystone/v2.0/users/1234567890',
                              headers=self.headers)
        self.assertEqual(res.status_code, 401)

    def test_user_delete_bad_request(self):
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
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.delete('http://localhost/keystone/v2.0/users/1234567890',
                              headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_user_delete(self):
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
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.delete('http://localhost/keystone/v2.0/users/{0}'
                              .format(tom),
                              headers=self.headers)
        self.assertEqual(res.status_code, 204)
