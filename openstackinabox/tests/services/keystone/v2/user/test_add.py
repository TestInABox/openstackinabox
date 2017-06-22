"""
Stack-In-A-Box: Basic Test
"""
import json
import unittest

import mock
import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneV2UserAdd(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserAdd, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
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
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            json_data = json.dumps(self.user_info)
            res = requests.post(
                'http://localhost/keystone/v2.0/users',
                data=json_data
            )
            self.assertEqual(res.status_code, 403)

    def test_user_add_invalid_token(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            json_data = json.dumps(self.user_info)
            self.headers['x-auth-token'] = 'new_token'
            res = requests.post(
                'http://localhost/keystone/v2.0/users',
                headers=self.headers,
                data=json_data
            )
            self.assertEqual(res.status_code, 401)

    def test_user_add_bad_request(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One')
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            del self.user_info['user']['username']
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 400)

    def test_user_add_same_user(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One'
            )
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            self.user_info['user']['username'] = 'tom'
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 409)

    def test_user_add_invalid_username(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One'
            )
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            self.user_info['user']['username'] = 'trinity$'
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 400)

    def test_user_add_no_password(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One'
            )
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            del self.user_info['user']['OS-KSADM:password']
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 201)

    def test_user_add_invalid_password(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One'
            )
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            self.user_info['user']['OS-KSADM:password'] = 'Inl0veWithNeo$'
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 400)

    def __fail_add_user(self, *args, **kwargs):
        raise Exception('mock error')

    def test_user_add_failed(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One')
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']

            with mock.patch(
                    'openstackinabox.models.keystone.db.users.'
                    'KeystoneDbUsers.add') as mok_keystone_model:
                mok_keystone_model.side_effect = Exception('mock error')
                res = requests.post('http://localhost/keystone/v2.0/users',
                                    headers=self.headers,
                                    data=json_data)
                self.assertEqual(res.status_code, 404)

    def test_user_add(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')
            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One'
            )
            tom = self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='tom',
                email='tom@theone.matrix',
                password='bluepill',
                apikey='iamnottheone',
                enabled=True
            )
            self.keystone.model.roles.add_user_role_by_role_name(
                tenant_id=neo_tenant_id,
                user_id=tom,
                role_name='identity:user-admin'
            )

            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users',
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 201)

            user_info = self.keystone.model.users.get_by_id(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            self.assertEqual(user_info['user_id'], tom)
            self.assertEqual(user_info['username'], 'tom')
            self.assertEqual(user_info['email'], 'tom@theone.matrix')
            self.assertEqual(user_info['password'], 'bluepill')
            self.assertEqual(user_info['apikey'], 'iamnottheone')
            self.assertTrue(user_info['enabled'])
