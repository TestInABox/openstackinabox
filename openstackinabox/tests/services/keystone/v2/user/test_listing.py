"""
Stack-In-A-Box: Basic Test
"""
import unittest

import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneV2UserListing(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserListing, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.tokens.admin_token
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserListing, self).tearDown()
        StackInABox.reset_services()

    def test_user_listing_no_token(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            res = requests.get('http://localhost/keystone/v2.0/users')
            self.assertEqual(res.status_code, 403)

    def test_user_listing_bad_token(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            self.headers['x-auth-token'] = 'new_token'
            res = requests.get('http://localhost/keystone/v2.0/users',
                               headers=self.headers)
            self.assertEqual(res.status_code, 401)

    def test_user_listing(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One')
            tom = self.keystone.model.users.add(
                neo_tenant_id,
                'tom',
                'tom@theone.matrix',
                'bluepill',
                'iamnottheone',
                enabled=True
            )

            self.keystone.model.roles.add_user_role_by_role_name(
                neo_tenant_id,
                tom,
                'identity:user-admin')
            self.keystone.model.tokens.add(neo_tenant_id, tom)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)

            self.headers['x-auth-token'] = user_data['token']
            res = requests.get('http://localhost/keystone/v2.0/users',
                               headers=self.headers)
            self.assertEqual(res.status_code, 200)
            user_data = res.json()

            self.assertEqual(len(user_data['users']), 1)

            self.keystone.model.users.add(
                neo_tenant_id,
                'neo',
                'neo@theone.matrix',
                'redpill',
                'iamtheone',
                enabled=True
            )

            res = requests.get('http://localhost/keystone/v2.0/users',
                               headers=self.headers)
            self.assertEqual(res.status_code, 200)
            user_data = res.json()

            self.assertEqual(len(user_data['users']), 2)

    def test_user_listing_by_name(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            neo_tenant_id = self.keystone.model.tenants.add(
                tenant_name='neo',
                description='The One')
            tom = self.keystone.model.users.add(
                neo_tenant_id,
                'tom',
                'tom@theone.matrix',
                'bluepill',
                'iamnottheone',
                enabled=True
            )

            self.keystone.model.roles.add_user_role_by_role_name(
                neo_tenant_id,
                tom,
                'identity:user-admin')
            self.keystone.model.tokens.add(neo_tenant_id, tom)
            user_data = self.keystone.model.tokens.get_by_user_id(tom)

            self.headers['x-auth-token'] = user_data['token']
            res = requests.get('http://localhost/keystone/v2.0/users',
                               headers=self.headers)
            self.assertEqual(res.status_code, 200)
            user_data = res.json()

            self.assertEqual(len(user_data['users']), 1)

            self.keystone.model.users.add(
                neo_tenant_id,
                'neo',
                'neo@theone.matrix',
                'redpill',
                'iamtheone',
                enabled=True
            )

            res = requests.get('http://localhost/keystone/v2.0/users?name=tom',
                               headers=self.headers)
            self.assertEqual(res.status_code, 200)
            user_data = res.json()

            self.assertIn('user', user_data)
            self.assertEqual(len(user_data), 1)
            self.assertEqual(user_data['user']['username'], 'tom')

    def test_user_listing_with_invalid_query_param(self):
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
            res = requests.get(
                'http://localhost/keystone/v2.0/users?honesty=False',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 200)
            user_data = res.json()

            self.assertEqual(len(user_data['users']), 1)

            self.keystone.model.users.add(
                tenant_id=neo_tenant_id,
                username='neo',
                email='neo@theone.matrix',
                password='redpill',
                apikey='iamtheone',
                enabled=True
            )

            res = requests.get(
                'http://localhost/keystone/v2.0/users',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 200)
            user_data = res.json()

            self.assertEqual(len(user_data['users']), 2)
