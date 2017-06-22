import uuid

import unittest

from stackinabox.stack import StackInABox

from openstackinabox.services.keystone import KeystoneV2Service


class TestKeystoneV2AuthBase(unittest.TestCase):

    @staticmethod
    def make_tenant_name():
        return 'tenant_{0}'.format(str(uuid.uuid4()))

    def setUp(self):
        super(TestKeystoneV2AuthBase, self).setUp()

        self.tenantname = self.make_tenant_name()
        self.keystone = KeystoneV2Service()
        self.username = 'user_{0}'.format(str(uuid.uuid4()))
        self.password = 'pAss{0}'.format(
            str(uuid.uuid4()).replace('-', '')
        )
        self.apikey = str(uuid.uuid4())
        self.email = '{0}@stackinabox.mock'.format(self.username)
        self.keystone.model.tenants.add(
            tenant_name=self.tenantname,
            description="test tenant"
        )
        tenant_data = self.keystone.model.tenants.get_by_name(
            tenant_name=self.tenantname
        )
        self.tenantid = tenant_data['id']

        self.keystone.model.users.add(
            tenant_id=self.tenantid,
            username=self.username,
            password=self.password,
            apikey=self.apikey,
            email=self.email
        )
        user_data = self.keystone.model.users.get_by_name(
            tenant_id=self.tenantid,
            username=self.username
        )
        self.userid = user_data['user_id']
        self.token = self.keystone.model.tokens.make_token()
        self.keystone.model.tokens.add(
            tenant_id=self.tenantid,
            user_id=self.userid,
            token=self.token
        )

        StackInABox.register_service(self.keystone)

    def tearDown(self):
        super(TestKeystoneV2AuthBase, self).tearDown()
        StackInABox.reset_services()

    def assertUserData(self, auth_response, user_id=None, username=None):
        self.assertIn('access', auth_response)
        self.assertIn('user', auth_response['access'])
        user_data = auth_response['access']['user']
        self.assertEqual(
            user_data['id'],
            user_id if user_id is not None else self.userid
        )
        self.assertEqual(
            user_data['name'],
            username if username is not None else self.username
        )

    def assertTokenData(self, auth_response, tenant_id=None, tenant_name=None):
        self.assertIn('access', auth_response)
        self.assertIn('token', auth_response['access'])
        token_data = auth_response['access']['token']

        self.assertIn('id', token_data)
        self.assertIn('expires', token_data)
        self.assertIn('tenant', token_data)
        self.assertIn('id', token_data['tenant'])
        self.assertIn('name', token_data['tenant'])

        self.assertEqual(
            token_data['tenant']['id'],
            tenant_id if tenant_id is not None else self.tenantid
        )
        self.assertEqual(
            token_data['tenant']['name'],
            tenant_name if tenant_name is not None else self.tenantname
        )

    def assertServiceCatalog(self, auth_response, length=0):
        self.assertIn('access', auth_response)
        self.assertIn('serviceCatalog', auth_response['access'])

        service_catalog = auth_response['access']['serviceCatalog']
        self.assertEqual(
            len(service_catalog),
            length
        )
