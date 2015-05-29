"""
Stack-In-A-Box: Add Credentials to User
"""

import json
import unittest

import mock
import requests
import stackinabox.util_requests_mock
from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneV2UserAddCredentials(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserAddCredentials, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        self.tenant_id = self.keystone.model.add_tenant(tenantname='neo',
                                                        description='The One')
        self.user_info = {
            'user': {
                'username': 'trinity',
                'enabled': True,
                'email': 'trinity@theone.matrix',
                'password': 'Inl0veWithNeo'
            }
        }
        self.user_info['user']['userid'] =\
            self.keystone.model.add_user(tenantid=self.tenant_id,
                                         username=self.user_info['user'][
                                             'username'],
                                         email=self.user_info['user']['email'],
                                         password=self.user_info['user'][
                                             'password'],
                                         enabled=self.user_info['user'][
                                             'enabled'])
        self.keystone.model.add_token(self.tenant_id,
                                      self.user_info['user']['userid'])
        self.keystone.model.add_user_role_by_rolename(
            tenantid=self.tenant_id,
            userid=self.user_info['user']['userid'],
            rolename=self.keystone.model.IDENTITY_ADMIN_ROLE)
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserAddCredentials, self).tearDown()
        StackInABox.reset_services()

    @staticmethod
    def get_userid_url(host, userid):
        return 'http://{0}/keystone/v2.0/users/{1}/OS-KSADM/credentials'\
               .format(host, userid)

    def test_user_add_credentials_basic(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestKeystoneV2UserAddCredentials.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            user_info = {
                'passwordCredentials': {
                    'username': self.user_info['user']['username'],
                    'password': 'Tr1n1tyR0ck$'
                }
            }

            json_data = json.dumps(user_info)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post(url,
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 201)

    def test_user_add_credentials_too_many_parameters(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestKeystoneV2UserAddCredentials.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            user_info = {
                'passwordCredentials': {
                    'enabled': False,
                    'username': self.user_info['user']['username'],
                    'password': 'Tr1n1tyR0ck$'
                }
            }

            json_data = json.dumps(user_info)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post(url,
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 201)

    def test_user_add_credentials_no_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            url = TestKeystoneV2UserAddCredentials.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            user_info = {
                'passwordCredentials': {
                    'username': self.user_info['user']['username'],
                    'password': 'Tr1n1tyR0ck$'
                }
            }

            json_data = json.dumps(user_info)
            res = requests.post(url, headers=None, data=json_data)
            self.assertEqual(res.status_code, 403)

    def test_user_add_credentials_invalid_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            url = TestKeystoneV2UserAddCredentials.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            user_info = {
                'passwordCredentials': {
                    'username': self.user_info['user']['username'],
                    'password': 'Tr1n1tyR0ck$'
                }
            }

            json_data = json.dumps(user_info)
            self.headers['x-auth-token'] = 'new_token'
            res = requests.post(url,
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 401)

    def test_user_add_credentials_invalid_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            url = TestKeystoneV2UserAddCredentials.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            user_info = {
                'credentials': {
                    'username': self.user_info['user']['username'],
                    'password': 'Tr1n1tyR0ck$'
                }
            }

            json_data = json.dumps(user_info)
            res = requests.post(url,
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 400)

    def test_user_add_credentials_invalid_user_id(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestKeystoneV2UserAddCredentials.get_userid_url(
                'localhost',
                (int(self.user_info['user']['userid']) + 1))

            user_info = {
                'passwordCredentials': {
                    'username': self.user_info['user']['username'],
                    'password': 'Tr1n1tyR0ck$'
                }
            }

            json_data = json.dumps(user_info)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post(url,
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 404)
