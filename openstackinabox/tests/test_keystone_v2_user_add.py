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
class TestKeystoneV2UserAdd(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserAdd, self).setUp()
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
        super(TestKeystoneV2UserAdd, self).tearDown()
        StackInABox.reset_services()

    def test_user_add_no_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        json_data = json.dumps(self.user_info)
        res = requests.post('http://localhost/keystone/v2.0/users',
                            data=json_data)
        self.assertEqual(res.status_code, 403)

    def test_user_add_invalid_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        json_data = json.dumps(self.user_info)
        self.headers['x-auth-token'] = 'new_token' 
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 401)

    def test_user_add_bad_request(self):
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
        del self.user_info['user']['username']
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 400)

    def test_user_add_same_user(self):
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
        self.user_info['user']['username'] = 'tom'
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 409)

    def test_user_add_invalid_username(self):
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
        self.user_info['user']['username'] = 'trinity$'
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 400)

    def test_user_add_no_password(self):
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
        del self.user_info['user']['OS-KSADM:password']
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 201)

    def test_user_add_invalid_password(self):
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
        self.user_info['user']['OS-KSADM:password'] = 'Inl0veWithNeo$'
        json_data = json.dumps(self.user_info)
        user_data = self.keystone.model.get_token_by_userid(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 400)

    def __fail_add_user(self, *args, **kwargs):
        raise Exception('mock error')

    def test_user_add_failed(self):
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
        
        with mock.patch(
                'openstackinabox.models.keystone.model.'
                'KeystoneModel.add_user') as mok_keystone_model:
            mok_keystone_model.side_effect = Exception('mock error')
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 404)

    def test_user_add(self):
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
        res = requests.post('http://localhost/keystone/v2.0/users',
                            headers=self.headers,
                            data=json_data)
        self.assertEqual(res.status_code, 201)

        user_info = self.keystone.model.get_user_by_id(neo_tenant_id,
                                                       tom)
        self.assertEqual(user_info['userid'], tom)
        self.assertEqual(user_info['username'], 'tom')
        self.assertEqual(user_info['email'], 'tom@theone.matrix')
        self.assertEqual(user_info['password'], 'bluepill')
        self.assertEqual(user_info['apikey'], 'iamnottheone')
        self.assertTrue(user_info['enabled'])

