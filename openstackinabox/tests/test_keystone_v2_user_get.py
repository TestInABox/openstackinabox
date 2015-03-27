"""
Stack-In-A-Box: Basic Test
"""
import json
import unittest

import httpretty
import mock
import requests
import stackinabox.util_httpretty
from stackinabox.stack import StackInABox

from openstackinabox.models.keystone.model import KeystoneModel
from openstackinabox.services.keystone import KeystoneV2Service


@httpretty.activate
class TestKeystoneV2UserGet(unittest.TestCase):

    def setUp(self):
        super(TestKeystoneV2UserGet, self).setUp()
        self.keystone = KeystoneV2Service()
        self.headers = {
            'x-auth-token': self.keystone.model.get_admin_token()
        }
        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2UserGet, self).tearDown()
        StackInABox.reset_services()

    def test_user_get_no_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        neo_tenant_id = self.keystone.model.add_tenant(tenantname='neo',
                                                         description='The One')
        tom = self.keystone.model.add_user(neo_tenant_id,
                                           'tom',
                                           'tom@theone.matrix',
                                           'bluepill',
                                           'iamnottheone',
                                           enabled=True)
        self.keystone.model.add_token(neo_tenant_id, tom)
        user_data = self.keystone.model.get_token_by_userid(tom)
        
        url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom)
        res = requests.get(url)
        self.assertEqual(res.status_code, 403)

    def test_user_get_invalid_token(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        neo_tenant_id = self.keystone.model.add_tenant(tenantname='neo',
                                                         description='The One')
        tom = self.keystone.model.add_user(neo_tenant_id,
                                           'tom',
                                           'tom@theone.matrix',
                                           'bluepill',
                                           'iamnottheone',
                                           enabled=True)
        self.keystone.model.add_token(neo_tenant_id, tom)
        user_data = self.keystone.model.get_token_by_userid(tom)
        
        url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom)
        self.headers['x-auth-token'] = 'new_token' 
        res = requests.get(url, headers=self.headers)
        self.assertEqual(res.status_code, 401)

    def test_user_get_bad_userid(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        neo_tenant_id = self.keystone.model.add_tenant(tenantname='neo',
                                                         description='The One')
        tom = self.keystone.model.add_user(neo_tenant_id,
                                           'tom',
                                           'tom@theone.matrix',
                                           'bluepill',
                                           'iamnottheone',
                                           enabled=True)
        self.keystone.model.add_token(neo_tenant_id, tom)
        user_data = self.keystone.model.get_token_by_userid(tom)
        
        url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom + 1)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.get(url, headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_user_get(self):
        stackinabox.util_httpretty.httpretty_registration('localhost')
        neo_tenant_id = self.keystone.model.add_tenant(tenantname='neo',
                                                       description='The One')
        tom = self.keystone.model.add_user(neo_tenant_id,
                                           'tom',
                                           'tom@theone.matrix',
                                           'bluepill',
                                           'iamnottheone',
                                           enabled=True)
        self.keystone.model.add_token(neo_tenant_id, tom)
        user_data = self.keystone.model.get_token_by_userid(tom)
        
        url = 'http://localhost/keystone/v2.0/users/{0}'.format(tom)
        self.headers['x-auth-token'] = user_data['token']
        res = requests.get(url, headers=self.headers)
        self.assertEqual(res.status_code, 200)
