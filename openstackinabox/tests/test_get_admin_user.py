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


class TestKeystoneV2GetAdmin(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2GetAdmin, self).setUp()
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
        self.session = requests.Session()

    def tearDown(self):
        super(TestKeystoneV2GetAdmin, self).tearDown()
        StackInABox.reset_services()
        self.session.close()

    @staticmethod
    def get_userid_url(host, userid):
        return 'http://{0}/keystone/v2.0/users/{1}/RAX-AUTH/admins'\
               .format(host, userid)

    def test_get_admin_user_basic(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestKeystoneV2GetAdmin.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            self.headers['x-auth-token'] = user_data['token']
            res = requests.get(url, headers=self.headers, data='')
            self.assertEqual(res.status_code, 200)

    def test_get_admin_user_incorrect_request(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestKeystoneV2GetAdmin.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            res = requests.get(url, headers=self.headers, data='')
            self.assertEqual(res.status_code, 404)

    def test_get_admin_user_no_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            url = TestKeystoneV2GetAdmin.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            res = requests.get(url, headers=None, data='')
            self.assertEqual(res.status_code, 403)

    def test_get_admin_user_invalid_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            
            url = TestKeystoneV2GetAdmin.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = 'new_token'
            res = requests.get(url, headers=self.headers, data='')
            self.assertEqual(res.status_code, 401)

    