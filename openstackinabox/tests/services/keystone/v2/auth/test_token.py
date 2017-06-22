"""
Stack-In-A-Box: Basic Test
"""
import json
import random

import ddt
import requests
import stackinabox.util.requests_mock.core

from openstackinabox.tests.services.keystone.v2.auth.base import (
    TestKeystoneV2AuthBase
)


@ddt.ddt
class TestKeystoneV2AuthToken(TestKeystoneV2AuthBase):

    def setUp(self):
        super(TestKeystoneV2AuthToken, self).setUp()

    def tearDown(self):
        super(TestKeystoneV2AuthToken, self).tearDown()

    @ddt.data(
        ('tenantId', 'tenantid'),
        ('tenantName', 'tenantname')
    )
    @ddt.unpack
    def test_token_tenantid(self, dictKey, attributeName):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    dictKey: getattr(self, attributeName),
                    'token': {
                        'id': self.token
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 200)

            result = res.json()
            self.assertUserData(result)
            self.assertTokenData(result, tenant_name=self.username)
            self.assertServiceCatalog(result)

    @ddt.data(
        ('tenantId', 'tenantid'),
        ('tenantName', 'tenantname')
    )
    @ddt.unpack
    def test_invalid_auth_request(self, dictKey, attributeName):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    dictKey: getattr(self, attributeName),
                    'badToken': {
                        'id': self.token
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 400)

    @ddt.data(
        ('tenantId', 'tenantid', 'attribute', 'invalid', 400),
        ('tenantName', 'tenantname', 'attribute', 'invalid', 400),

        ('tenantId', 'tenantid', 'attribute', 'replace', 403),
        ('tenantName', 'tenantname', 'attribute', 'replace', 403),

        ('tenantId', 'tenantid', 'auth', 'n/a', 400),
        ('tenantName', 'tenantname', 'auth', 'n/a', 400)
    )
    @ddt.unpack
    def test_token_auth_bad_value(self, dictKey, attributeName, whats_invalid,
                                  invalid_how, expected_status_code):
        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    dictKey: getattr(self, attributeName),
                    'token': {
                        'id': self.token
                    }
                }
            }

            if whats_invalid == 'attribute':
                new_value = None
                if attributeName == 'tenantid':
                    if invalid_how == 'invalid':
                        new_value = str(self.tenantid)
                    elif invalid_how == 'replace':
                        new_value = random.randint(100, 100000)
                elif attributeName == 'tenantname':
                    if invalid_how == 'invalid':
                        new_value = '123_{0}'.format(self.make_tenant_name())
                    elif invalid_how == 'replace':
                        new_value = self.make_tenant_name()

                auth_data['auth'][dictKey] = new_value
            elif whats_invalid == 'auth':
                auth_data['mixedup'] = auth_data['auth']
                del auth_data['auth']

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, expected_status_code)

    @ddt.data(
        ('tenantId', 'tenantid'),
        ('tenantName', 'tenantname')
    )
    @ddt.unpack
    def test_token_auth_disabled_user(self, dictKey, attributeName):
        self.keystone.model.tenants.update_status(
            tenant_id=self.tenantid,
            enabled=False
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    dictKey: getattr(self, attributeName),
                    'token': {
                        'id': self.token
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 403)

    @ddt.data(
        ('tenantId', 'tenantid'),
        ('tenantName', 'tenantname')
    )
    @ddt.unpack
    def test_token_auth_invalid_token(self, dictKey, attributeName):
        self.keystone.model.tenants.update_status(
            tenant_id=self.tenantid,
            enabled=False
        )
        self.keystone.model.tokens.delete(
            tenant_id=self.tenantid,
            user_id=self.userid
        )

        with stackinabox.util.requests_mock.core.activate():
            stackinabox.util.requests_mock.core.requests_mock_registration(
                'localhost')

            auth_data = {
                'auth': {
                    dictKey: getattr(self, attributeName),
                    'token': {
                        'id': self.keystone.model.tokens.make_token()
                    }
                }
            }

            res = requests.post(
                'http://localhost/keystone/v2.0/tokens',
                data=json.dumps(auth_data)
            )
            self.assertEqual(res.status_code, 401)
