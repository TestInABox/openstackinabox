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


class TestKeystoneV2UserUpdate(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserUpdate, self).setUp()
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
                'OS-KSADM:password': 'Inl0veWithNeo'
            }
        }
        self.user_info['user']['userid'] =\
            self.keystone.model.add_user(tenantid=self.tenant_id,
                                         username=self.user_info['user'][
                                             'username'],
                                         email=self.user_info['user']['email'],
                                         password=self.user_info['user'][
                                             'OS-KSADM:password'],
                                         enabled=self.user_info['user'][
                                             'enabled'])
        self.keystone.model.add_token(self.tenant_id,
                                      self.user_info['user']['userid'])
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserUpdate, self).tearDown()
        StackInABox.reset_services()

    def test_user_update_no_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                data=json_data)
            self.assertEqual(res.status_code, 403)

    def test_user_update_invalid_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            self.headers['x-auth-token'] = 'new_token'
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json_data)
            self.assertEqual(res.status_code, 401)

    def test_user_update_no_user(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps({'family': {}}))
            self.assertEqual(res.status_code, 400)

    def test_user_update_no_user_id(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps({'user': {}}))
            self.assertEqual(res.status_code, 400)

    def test_user_update_invalid_user_id(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            self.user_info['user']['userid'] = '1234567890'
            self.user_info['user']['email'] = 'trinity@lost.matrix'
            self.user_info['user']['id'] = self.user_info['user']['userid']
            self.user_info['user']['enabled'] = False
            self.user_info['user']['OS-KSADM:password'] = 'neocortex'
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps(self.user_info))
            self.assertEqual(res.status_code, 404)

    def test_user_update(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            self.user_info['user']['email'] = 'trinity@lost.matrix'
            self.user_info['user']['id'] = self.user_info['user']['userid']
            self.user_info['user']['enabled'] = False
            self.user_info['user']['OS-KSADM:password'] = 'neocortex'
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps(self.user_info))
            self.assertEqual(res.status_code, 200)

    def test_user_update_no_enabled(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            self.user_info['user']['email'] = 'trinity@lost.matrix'
            self.user_info['user']['id'] = self.user_info['user']['userid']
            del self.user_info['user']['enabled']
            self.user_info['user']['OS-KSADM:password'] = 'neocortex'
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps(self.user_info))
            self.assertEqual(res.status_code, 200)

    def test_user_update_no_email(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            del self.user_info['user']['email']
            self.user_info['user']['id'] = self.user_info['user']['userid']
            self.user_info['user']['enabled'] = False
            self.user_info['user']['OS-KSADM:password'] = 'neocortex'
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps(self.user_info))
            self.assertEqual(res.status_code, 200)

    def test_user_update_no_password(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            json_data = json.dumps(self.user_info)
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = user_data['token']
            self.user_info['user']['email'] = 'trinity@lost.matrix'
            self.user_info['user']['id'] = self.user_info['user']['userid']
            self.user_info['user']['enabled'] = False
            del self.user_info['user']['OS-KSADM:password']
            res = requests.post('http://localhost/keystone/v2.0/users/{0}'
                                .format(self.user_info['user']['userid']),
                                headers=self.headers,
                                data=json.dumps(self.user_info))
            self.assertEqual(res.status_code, 200)
