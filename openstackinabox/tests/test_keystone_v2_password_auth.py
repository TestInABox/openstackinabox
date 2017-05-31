"""
Stack-In-A-Box: Basic Test
"""
import json
import random
import unittest
import uuid

import ddt
import mock
import requests
import stackinabox.util.requests_mock.core
from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


@ddt.ddt
class TestKeystoneV2AuthPassword(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2AuthPassword, self).setUp()
        self.keystone = KeystoneV2Service()
        self.username = 'user_{0}'.format(str(uuid.uuid4()))
        self.password = 'pAss{0}'.format(
            str(uuid.uuid4()).replace('-', '')
        )
        self.apikey = str(uuid.uuid4())
        self.email = '{0}@stackinabox.mock'.format(self.username)
        self.tenantid = random.randint(100, 10000)

        self.keystone.model.add_user(
            tenantid=self.tenantid,
            username=self.username,
            password=self.password,
            apikey=self.apikey,
            email=self.email
        )

        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2AuthPassword, self).tearDown()
        StackInABox.reset_services()

    def test_password_auth(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    'passwordCredentials': {
                        'username': self.username,
                        'password': self.password
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 200)

    def test_invalid_auth_request(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    'badPasswordCredentials': {
                        'username': self.username,
                        'password': self.password
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 400)

    @ddt.data(
        ('auth', 400),
        ('password', 401),
        ('username', 404),
        ('value-password', 400),
        ('value-username', 400)
    )
    @ddt.unpack
    def test_password_auth_bad_value(self, whats_invalid,
                                     expected_status_code):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    'passwordCredentials': {
                        'username': self.username,
                        'password': self.password
                    }
                }
            }

            if whats_invalid == 'password':
                auth_data['auth']['passwordCredentials']['password'] = (
                    'someBadPassword123'
                )
            elif whats_invalid == 'username':
                auth_data['auth']['passwordCredentials']['username'] = (
                    'someOtherUser'
                )
            elif whats_invalid == 'auth':
                auth_data['mixedup'] = auth_data['auth']
                del auth_data['auth']
            elif whats_invalid.startswith('value'):
                unused, invalid_value_key = whats_invalid.split('-')
                if invalid_value_key == 'username':
                    auth_data['auth']['passwordCredentials']['username'] = (
                        '123someOtherUser'
                    )
                elif invalid_value_key == 'password':
                    auth_data['auth']['passwordCredentials']['password'] = (
                        '\ someBadPassword'
                    )

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, expected_status_code)

    def test_password_auth_disabled_user(self):
        second_user = 'user_{0}'.format(str(uuid.uuid4()))

        self.keystone.model.add_user(
            tenantid=self.tenantid,
            username=second_user,
            password=self.password,
            apikey=self.apikey,
            email=self.email,
            enabled=False
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    'passwordCredentials': {
                        'username': second_user,
                        'password': self.password
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 403)
