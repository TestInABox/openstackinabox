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
class TestKeystoneV2AuthApiKey(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2AuthApiKey, self).setUp()
        self.dictApiKey = 'RAX-KSKEY:apiKeyCredentials'

        self.keystone = KeystoneV2Service()
        self.username = 'user_{0}'.format(str(uuid.uuid4()))
        self.password = 'pAss{0}'.format(
            str(uuid.uuid4()).replace('-', '')
        )
        self.apikey = str(uuid.uuid4())
        self.email = '{0}@stackinabox.mock'.format(self.username)
        self.tenantid = random.randint(100, 10000)

        self.keystone.model.users.add(
            tenant_id=self.tenantid,
            username=self.username,
            password=self.password,
            apikey=self.apikey,
            email=self.email
        )

        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2AuthApiKey, self).tearDown()
        StackInABox.reset_services()

    def test_apikey_auth(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    self.dictApiKey: {
                        'username': self.username,
                        'apiKey': self.apikey
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 200)

            result = res.json()
            token = result['access']['token']
            user = result['access']['user']
            serviceCatalog = result['access']['serviceCatalog']

            self.assertEqual(0, len(serviceCatalog))
            self.assertEqual(self.tenantid, token['tenant']['id'])
            self.assertEqual(self.username, token['tenant']['name'])
            self.assertEqual(self.username, user['name'])


    def test_invalid_auth_request(self):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    'badPasswordCredentials': {
                        'username': self.username,
                        'apiKey': self.apikey
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
        ('apiKey', 401),
        ('username', 404),
        ('value-apiKey', 400),
        ('value-username', 400)
    )
    @ddt.unpack
    def test_apikey_auth_bad_value(self, whats_invalid,
                                   expected_status_code):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    self.dictApiKey: {
                        'username': self.username,
                        'apiKey': self.apikey
                    }
                }
            }

            if whats_invalid == 'apiKey':
                auth_data['auth'][self.dictApiKey]['apiKey'] = (
                    'someBadPassword123'
                )
            elif whats_invalid == 'username':
                auth_data['auth'][self.dictApiKey]['username'] = (
                    'someOtherUser'
                )
            elif whats_invalid == 'auth':
                auth_data['mixedup'] = auth_data['auth']
                del auth_data['auth']
            elif whats_invalid.startswith('value'):
                unused, invalid_value_key = whats_invalid.split('-')
                if invalid_value_key == 'username':
                    auth_data['auth'][self.dictApiKey]['username'] = (
                        '123someOtherUser'
                    )
                elif invalid_value_key == 'apiKey':
                    auth_data['auth'][self.dictApiKey]['apiKey'] = (
                        1234567890  # non-string value
                    )

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, expected_status_code)

    def test_apikey_auth_disabled_user(self):
        second_user = 'user_{0}'.format(str(uuid.uuid4()))

        self.keystone.model.users.add(
            tenant_id=self.tenantid,
            username=second_user,
            password=self.apikey,
            apikey=self.apikey,
            email=self.email,
            enabled=False
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    self.dictApiKey: {
                        'username': second_user,
                        'apiKey': self.apikey
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 403)
