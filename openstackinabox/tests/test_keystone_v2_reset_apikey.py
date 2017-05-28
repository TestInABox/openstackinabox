import unittest
import json

import requests

import stackinabox.util_requests_mock
from stackinabox.stack import StackInABox
from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


class TestResetAPIKeys(unittest.TestCase):

    def setUp(self):
        super(TestResetAPIKeys, self).setUp()
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
                'password': 'Inl0veWithNeo',
                'apikey': '987654321zzz',
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
                                             'enabled'],
                                         apikey=self.user_info['user']['apikey'])
        self.keystone.model.add_token(self.tenant_id,
                                      self.user_info['user']['userid'])
        self.keystone.model.add_user_role_by_rolename(
            tenantid=self.tenant_id,
            userid=self.user_info['user']['userid'],
            rolename=self.keystone.model.IDENTITY_ADMIN_ROLE)
        StackInABox.register_service(self.keystone)
        self.session = requests.Session()

    def tearDown(self):
        super(TestResetAPIKeys, self).tearDown()
        StackInABox.reset_services()
        self.session.close()

    @staticmethod
    def get_userid_url(host, userid):
        return 'http://{0}/keystone/v2.0/users/{1}/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials/RAX-AUTH/reset'\
               .format(host, userid)

    def test_reset_apikey_basic(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')
            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestResetAPIKeys.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            self.headers['x-auth-token'] = user_data['token']
            res = requests.post(url, headers=self.headers, data='')
            self.assertEqual(res.status_code, 200)

    def test_reset_apikey_incorrect_request(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            user_data = self.keystone.model.get_token_by_userid(
                self.user_info['user']['userid'])

            url = TestResetAPIKeys.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            res = requests.post(url, headers=self.headers, data='')
            self.assertEqual(res.status_code, 404)

    def test_reset_apikey_no_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            url = TestResetAPIKeys.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])

            res = requests.post(url, headers=None, data='')
            self.assertEqual(res.status_code, 403)

    def test_reset_apikey_invalid_token(self):
        with stackinabox.util_requests_mock.activate():
            stackinabox.util_requests_mock.requests_mock_registration(
                'localhost')

            url = TestResetAPIKeys.get_userid_url(
                'localhost',
                self.user_info['user']['userid'])
            self.headers['x-auth-token'] = 'new_token'
            res = requests.post(url, headers=self.headers, data='')
            self.assertEqual(res.status_code, 401)
