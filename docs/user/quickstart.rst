.. _quickstart:

Quick Start
===========

Install OpenStack-In-A-Box per :ref:`install` before continuing.

Running a Test
--------------

We'll borrow the ```requests-mock``` example from the README.rst to show how
to use the OpenStack-In-A-Box in an actual test:

.. code-block:: python

    import unittest

    import requests

    import stackinabox.util.requests_mock
    from stackinabox.stack import StackInABox

    from openstackinabox.models.keystone.model import KeystoneModel
    from openstackinabox.services.keystone import KeystoneV2Service

    class TestRequestsMock(unittest.TestCase):

        @staticmethod
        def make_tenant_name():
            return 'tenant_{0}'.format(str(uuid.uuid4()))

        def setUp(self):
            super(TestRequestsMock, self).setUp()

            self.keystone = KeystoneV2Service()

            # Create the tenant information
            self.tenantname = self.make_tenant_name()
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

            # Create the user information
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

            # Add a token
            self.token = self.keystone.model.tokens.make_token()
            self.keystone.model.tokens.add(
                tenant_id=self.tenantid,
                user_id=self.userid,
                token=self.token
            )

            StackInABox.register_service(self.keystone)
            self.session = requests.Session()

        def tearDown(self):
            super(TestRequestsMock, self).tearDown()
            StackInABox.reset_services()
            self.session.close()

        def test_basic_requests_mock(self):
            with stackinabox.util.requests_mock.core.activate():
                stackinabox.util.requests_mock.\
                    requests_mock_session_registration(
                        'localhost', self.session)

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
                # token info, user info, and service catalog
