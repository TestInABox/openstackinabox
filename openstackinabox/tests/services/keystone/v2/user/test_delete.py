"""
Stack-In-A-Box: Basic Test
"""
import unittest

import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneV2UserDelete(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserDelete, self).setUp()
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
        super(TestKeystoneV2UserDelete, self).tearDown()
        StackInABox.reset_services()

    def test_user_delete_no_token(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            res = requests.delete(
                'http://localhost/keystone/v2.0/users/1234567890'
            )
            self.assertEqual(res.status_code, 403)

    def test_user_delete_invalid_token(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost'
            )
            self.headers['x-auth-token'] = 'new_token'
            res = requests.delete(
                'http://localhost/keystone/v2.0/users/1234567890',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 401)

    def test_user_delete_bad_request(self):
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
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.delete(
                'http://localhost/keystone/v2.0/users/1234567890',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 404)

    def test_user_delete(self):
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
            user_data = self.keystone.model.tokens.get_by_user_id(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.delete(
                'http://localhost/keystone/v2.0/users/{0}'.format(tom),
                headers=self.headers
            )
            self.assertEqual(res.status_code, 204)
