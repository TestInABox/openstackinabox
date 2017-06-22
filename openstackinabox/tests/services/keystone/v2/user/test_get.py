"""
Stack-In-A-Box: Basic Test
"""
import unittest

import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneV2UserGet(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserGet, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserGet, self).tearDown()
        StackInABox.reset_services()

    def test_user_get_no_token(self):
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
            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            self.keystone.model.tokens.get_by_user_id(tom)

            url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom)
            res = requests.get(url)
            self.assertEqual(res.status_code, 403)

    def test_user_get_invalid_token(self):
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
            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            self.keystone.model.tokens.get_by_user_id(tom)

            url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom)
            self.headers['x-auth-token'] = 'new_token'
            res = requests.get(url, headers=self.headers)
            self.assertEqual(res.status_code, 401)

    def test_user_get_bad_userid(self):
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
            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            user_data = self.keystone.model.tokens.get_by_user_id(tom)

            url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom + 1)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.get(url, headers=self.headers)
            self.assertEqual(res.status_code, 404)

    def test_user_get(self):
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
            self.keystone.model.tokens.add(
                tenant_id=neo_tenant_id,
                user_id=tom
            )
            user_data = self.keystone.model.tokens.get_by_user_id(tom)

            url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom)
            self.headers['x-auth-token'] = user_data['token']
            res = requests.get(url, headers=self.headers)
            self.assertEqual(res.status_code, 200)
