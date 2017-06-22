import mock

import ddt
import six

from openstackinabox.tests.base import TestBase

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.model import (
    schema,
    KeystoneModel
)


@ddt.ddt
class TestKeystoneModel(TestBase):

    def setUp(self):
        super(TestKeystoneModel, self).setUp(initialize=False)
        self.model = KeystoneModel
        self.db = self.master_model.database

    def tearDown(self):
        super(TestKeystoneModel, self).tearDown()

    def test_initialize_db_schema(self):
        db_cursor = mock.MagicMock()
        db_execute = mock.MagicMock()
        db_commit = mock.MagicMock()
        db_instance = mock.MagicMock()
        db_instance.cursor.return_value = db_cursor
        db_instance.commit = db_commit
        db_cursor.execute = db_execute

        self.model.initialize_db_schema(db_instance)
        self.assertTrue(db_instance.cursor.called)
        self.assertTrue(db_execute.called)
        self.assertTrue(db_commit.called)
        self.assertEqual(db_execute.call_count, len(schema))
        for s in schema:
            db_execute.assert_any_call(s)

    def test_get_child_models(self):
        master = 'alpha'
        db = 'omega'

        child_models = self.model.get_child_models(master, db)
        self.assertEqual(len(child_models), len(self.model.CHILD_MODELS))

        def assert_has_instance(model_name, model_class):
            for cm_name, cm_instance in six.iteritems(child_models):
                if isinstance(cm_instance, model_class):
                    return
            self.assertFalse(
                True,
                msg="instance of {0} ({1}) not in list".format(
                    model_name,
                    model_class
                )
            )

        for child_model_name, child_model_type in six.iteritems(
            self.model.CHILD_MODELS
        ):
            assert_has_instance(child_model_name, child_model_type)

    def test_initialization(self):
        self.assertIsNone(self.master_model.roles.admin_role_id)
        self.assertIsNone(self.master_model.roles.viewer_role_id)
        self.assertIsNone(self.master_model.tenants.admin_tenant_id)
        self.assertIsNone(self.master_model.users.admin_user_id)
        self.assertIsNone(self.master_model.tokens.admin_token)

        self.master_model.init_database()

        self.assertIsNotNone(self.master_model.roles.admin_role_id)
        self.assertIsNotNone(self.master_model.roles.viewer_role_id)
        self.assertIsNotNone(self.master_model.tenants.admin_tenant_id)
        self.assertIsNotNone(self.master_model.users.admin_user_id)
        self.assertIsNotNone(self.master_model.tokens.admin_token)

        token_data = self.master_model.tokens.get_by_user_id(
            user_id=self.master_model.users.admin_user_id
        )
        self.assertEqual(
            token_data['tenant_id'],
            self.master_model.tenants.admin_tenant_id
        )
        self.assertEqual(
            token_data['user_id'],
            self.master_model.users.admin_user_id
        )
        self.assertEqual(
            token_data['token'],
            self.master_model.tokens.admin_token
        )
        self.assertFalse(token_data['revoked'])

    def test_properties(self):
        self.master_model.init_database()
        self.assertEqual(
            self.master_model.child_models['users'],
            self.master_model.users
        )
        self.assertEqual(
            self.master_model.child_models['tenants'],
            self.master_model.tenants
        )
        self.assertEqual(
            self.master_model.child_models['tokens'],
            self.master_model.tokens
        )
        self.assertEqual(
            self.master_model.child_models['roles'],
            self.master_model.roles
        )
        self.assertEqual(
            self.master_model.child_models['services'],
            self.master_model.services
        )
        self.assertEqual(
            self.master_model.child_models['endpoints'],
            self.master_model.endpoints
        )

    @ddt.data(
        0,
        1
    )
    def test_validate_token_admin(self, extra_role_count):
        self.master_model.init_database()

        with self.assertRaises(exceptions.KeystoneInvalidTokenError):
            self.master_model.validate_token_admin('foobar')

        tenant_id = self.master_model.tenants.add(
            tenant_name='foo',
            description='bar',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='bar',
            email='foo@bar',
            password='bar',
            apikey='foo',
            enabled=True
        )
        self.master_model.tokens.add(
            tenant_id=tenant_id,
            user_id=user_id,
            token='foobar'
        )

        with self.assertRaises(exceptions.KeystoneInvalidTokenError):
            self.master_model.validate_token_admin('foobar')

        role_names = [
            'role_{0}'.format(x)
            for x in range(extra_role_count)
        ]
        role_data = [
            {
                'name': role_name,
                'id': self.master_model.roles.add(role_name)
            }
            for role_name in role_names
        ]
        for role in role_data:
            self.master_model.roles.add_user_role_by_id(
                tenant_id=tenant_id,
                user_id=user_id,
                role_id=role['id']
            )

        self.master_model.roles.add_user_role_by_id(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=self.master_model.roles.admin_role_id
        )

        validation_user_data = self.master_model.validate_token_admin('foobar')
        self.assertEqual(validation_user_data['tenantid'], tenant_id)
        self.assertEqual(validation_user_data['userid'], user_id)
        self.assertEqual(validation_user_data['token'], 'foobar')

    def test_validate_token_service_admin(self):
        self.master_model.init_database()

        tenant_id = self.master_model.tenants.add(
            tenant_name='foo',
            description='bar',
            enabled=True
        )
        user_id = self.master_model.users.add(
            tenant_id=tenant_id,
            username='bar',
            email='foo@bar',
            password='bar',
            apikey='foo',
            enabled=True
        )
        self.master_model.tokens.add(
            tenant_id=tenant_id,
            user_id=user_id,
            token='foobar'
        )

        self.master_model.roles.add_user_role_by_id(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=self.master_model.roles.admin_role_id
        )

        with self.assertRaises(exceptions.KeystoneInvalidTokenError):
            self.master_model.validate_token_service_admin('foobar')

        user_data = self.master_model.validate_token_service_admin(
            self.master_model.tokens.admin_token
        )
        self.assertEqual(
            user_data['tenantid'],
            self.master_model.tenants.admin_tenant_id
        )
        self.assertEqual(
            user_data['userid'],
            self.master_model.users.admin_user_id
        )
        self.assertEqual(
            user_data['token'],
            self.master_model.tokens.admin_token
        )


@ddt.ddt
class TestKeystoneModelServiceCatalog(TestBase):

    def setUp(self):
        super(TestKeystoneModelServiceCatalog, self).setUp(initialize=False)
        self.model = KeystoneModel
        self.db = self.master_model.database
        self.master_model.init_database()
        self.token = 'f1gur3f0ll0w$f4$h10n'

        self.tenant_info = {
            'name': 'foo',
            'description': 'bar',
            'enabled': True
        }
        self.user_info = {
            'username': 'bar',
            'email': 'foo@bar',
            'password': 'b4R',
            'apikey': 'foo',
            'enabled': True
        }

        self.tenant_id = self.master_model.tenants.add(
            tenant_name=self.tenant_info['name'],
            description=self.tenant_info['description'],
            enabled=self.tenant_info['enabled']
        )
        self.user_id = self.master_model.users.add(
            tenant_id=self.tenant_id,
            username=self.user_info['username'],
            email=self.user_info['email'],
            password=self.user_info['password'],
            apikey=self.user_info['apikey'],
            enabled=self.user_info['enabled']
        )
        self.master_model.tokens.add(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            token=self.token
        )

        self.user_data = self.master_model.users.get_by_id(
            tenant_id=self.tenant_id,
            user_id=self.user_id
        )
        self.token_data = self.master_model.tokens.validate_token(
            self.token
        )

    def tearDown(self):
        super(TestKeystoneModelServiceCatalog, self).tearDown()

    def generate_roles(self, role_count):
        role_names = [
            'role_{0}'.format(x)
            for x in range(role_count)
        ]
        role_data = [
            {
                'name': role_name,
                'id': self.master_model.roles.add(role_name)
            }
            for role_name in role_names
        ]
        for role in role_data:
            self.master_model.roles.add_user_role_by_id(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                role_id=role['id']
            )

        return (
            role_names,
            role_data,
        )

    def generate_services(
        self, service_count, endpoint_count, endpoint_url_count,
        has_region=True, has_version_info=True, has_version_list=True,
        has_version_id=True
    ):
        services = {
            'service_{0}'.format(sn): {
                'description': 'test service {0}'.format(sn),
                'endpoints': [
                    {
                        'name': 'endpoint_{0}'.format(epn),
                        'region': 'r{0}'.format(epn) if has_region else None,
                        'version_info': (
                            'version.info' if has_version_info else None
                        ),
                        'version_list': (
                            'version.list' if has_version_list else None
                        ),
                        'version_id': str(epn) if has_version_id else None,
                        'urls': [
                            {
                                'name': 'url_{0}'.format(urln),
                                'url': 'ur.l/{0}'.format(urln)
                            }
                            for urln in range(endpoint_url_count)
                        ]
                    }
                    for epn in range(endpoint_count)
                ]
            }
            for sn in range(service_count)
        }

        for service_name, service_info in six.iteritems(services):
            services[service_name]['id'] = self.master_model.services.add(
                service_name,
                service_info['description']
            )
            for endpoint_info in service_info['endpoints']:
                endpoint_info['id'] = self.master_model.endpoints.add(
                    services[service_name]['id'],
                    endpoint_info['region'],
                    endpoint_info['version_info'],
                    endpoint_info['version_list'],
                    endpoint_info['version_id']
                )
                for endpoint_url_info in endpoint_info['urls']:
                    endpoint_url_info['id'] = (
                        self.master_model.endpoints.add_url(
                            endpoint_info['id'],
                            endpoint_url_info['name'],
                            endpoint_url_info['url']
                        )
                    )

        return services

    def check_service_catalog_auth_section(self, auth_entry):
        self.assertEqual(auth_entry['id'], self.token_data['token'])
        self.assertEqual(auth_entry['expires'], self.token_data['expires'])
        self.assertEqual(auth_entry['tenant']['id'], self.tenant_id)
        self.assertEqual(
            auth_entry['tenant']['name'], self.user_data['username']
        )

    def check_service_catalog_user_entry(
        self, role_count, role_names, role_data, user_entry
    ):
        self.assertEqual(user_entry['id'], self.user_id)
        self.assertEqual(user_entry['name'], self.user_data['username'])
        self.assertEqual(len(user_entry['roles']), role_count)

        def assertRoleInList(role_id, role_name):
            for role in role_data:
                if role['id'] == role_id and role['name'] == role_name:
                    # found it
                    return

            # failed to find it, so assert
            self.assertFalse(
                True,
                msg=(
                    'Unable to find role ({0} - {1}) in role_data'.format(
                        role_id,
                        role_name
                    )
                )
            )

        for role_entry in user_entry['roles']:
            assertRoleInList(
                role_entry['id'],
                role_entry['name']
            )

    def check_service_catalog_services(self, services, services_entries):
        self.assertEqual(len(services), len(services_entries))
        for service_info in services_entries:
            self.assertIn(service_info['name'], services)
            self.assertEqual(
                service_info['type'],
                services[service_info['name']]['description']
            )
            self.assertEqual(
                len(service_info['endpoints']),
                len(services[service_info['name']]['endpoints'])
            )
            for endpoint_info in service_info['endpoints']:
                found_endpoint = False
                for endpoint_data in (
                    services[service_info['name']]['endpoints']
                ):
                    if (
                        endpoint_info['region'] == endpoint_data['region'] and
                        endpoint_info['versionId'] == endpoint_data[
                            'version_id'] and
                        endpoint_info['versionList'] == endpoint_data[
                            'version_list'] and
                        endpoint_info['versionInfo'] == endpoint_data[
                            'version_info']
                    ):
                        for url_data in endpoint_data['urls']:
                            self.assertIn(url_data['name'], endpoint_info)
                            self.assertEqual(
                                url_data['url'],
                                endpoint_info[url_data['name']]
                            )
                        found_endpoint = True

                self.assertTrue(
                    found_endpoint,
                    msg=(
                        "Unable to find endpoint data: {0}, {1}".format(
                            endpoint_data,
                            endpoint_info
                        )
                    )
                )

    def check_service_catalog(
        self, role_count, role_names, role_data, services, service_catalog,
    ):
        self.check_service_catalog_auth_section(
            service_catalog['token']
        )
        self.check_service_catalog_user_entry(
            role_count, role_names, role_data, service_catalog['user']
        )
        self.check_service_catalog_services(
            services, service_catalog['serviceCatalog']
        )

    def test_service_catalog_auth_entry(self):
        self.assertEqual(self.token_data['token'], self.token)
        auth_entry = self.master_model.get_auth_token_entry(
            self.token_data,
            self.user_data
        )
        self.check_service_catalog_auth_section(auth_entry)

    @ddt.data(
        0,
        1,
        10,
        20
    )
    def test_service_catalog_user_entry(self, role_count):
        role_names, role_data = self.generate_roles(role_count)
        user_entry = self.master_model.get_auth_user_entry(
            self.user_data
        )
        self.check_service_catalog_user_entry(
            role_count, role_names, role_data, user_entry
        )

    @ddt.data(
        (0, 0, 0, True, True, True, True),
        (1, 0, 0, True, True, True, True),
        (1, 1, 0, True, True, True, True),
        (5, 4, 0, True, True, True, True),
        (5, 10, 0, True, True, True, True),
        (0, 0, 1, True, True, True, True),
        (1, 0, 1, True, True, True, True),
        (1, 1, 1, True, True, True, True),
        (5, 4, 1, True, True, True, True),
        (5, 10, 1, True, True, True, True),
        (1, 3, 2, False, True, True, True),
        (1, 3, 2, True, False, True, True),
        (1, 3, 2, True, True, False, True),
        # TODO: Fix the below test cases
        # (1, 3, 2, True, True, True, False),
        # (1, 3, 2, False, False, False, False),
    )
    @ddt.unpack
    def test_service_catalog_services_entry(
        self, service_count, endpoint_count, endpoint_url_count,
        has_region, has_version_info, has_version_list, has_version_id
    ):
        services = self.generate_services(
            service_count, endpoint_count, endpoint_url_count,
            has_region, has_version_info, has_version_list, has_version_id
        )
        services_entries = self.master_model.get_auth_service_catalog(
            self.user_data
        )
        self.check_service_catalog_services(services, services_entries)

    @ddt.data(
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (5, 10, 3, 4),
        (2, 20, 15, 10)
    )
    @ddt.unpack
    def test_service_catalog_services_entry_2(
        self, role_count, service_count, endpoint_count, endpoint_url_count
    ):
        role_names, role_data = self.generate_roles(role_count)

        services = self.generate_services(
            service_count, endpoint_count, endpoint_url_count
        )

        service_catalog = self.master_model.get_service_catalog(
            self.token_data,
            self.user_data
        )
        self.check_service_catalog(
            role_count, role_names, role_data, services, service_catalog
        )

    def test_password_auth_failures(self):
        with self.assertRaises(exceptions.KeystoneUserError):
            password_data = {
                'username': '43failme',
                'password': self.user_info['password']
            }
            self.master_model.password_authenticate(
                password_data
            )

        with self.assertRaises(exceptions.KeystoneUserError):
            password_data = {
                'username': self.user_info['username'],
                'password': '$$$$'
            }
            self.master_model.password_authenticate(
                password_data
            )

        with self.assertRaises(exceptions.KeystoneUserInvalidPasswordError):
            password_data = {
                'username': self.user_info['username'],
                'password': self.user_info['password'] + 'a'
            }
            self.master_model.password_authenticate(
                password_data
            )

        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            password_data = {
                'username': self.user_info['username'] + 'a',
                'password': self.user_info['password']
            }
            self.master_model.password_authenticate(
                password_data
            )

        with self.assertRaises(exceptions.KeystoneUserInvalidPasswordError):
            password_data = {
                'username': self.user_info['username'],
                'password': self.user_info['password'] + 'a'
            }
            self.master_model.password_authenticate(
                password_data
            )

        with self.assertRaises(exceptions.KeystoneDisabledUserError):
            self.master_model.users.update_by_id(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                email=self.user_info['email'],
                password=self.user_info['password'],
                apikey=self.user_info['apikey'],
                enabled=False
            )
            password_data = {
                'username': self.user_info['username'],
                'password': self.user_info['password']
            }
            self.master_model.password_authenticate(
                password_data
            )

        self.master_model.users.update_by_id(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            email=self.user_info['email'],
            password=self.user_info['password'],
            apikey=self.user_info['apikey'],
            enabled=True
        )

    @ddt.data(
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (5, 10, 3, 4),
        (2, 20, 15, 10)
    )
    @ddt.unpack
    def test_password_auth(
        self, role_count, service_count, endpoint_count, endpoint_url_count
    ):
        role_names, role_data = self.generate_roles(role_count)

        services = self.generate_services(
            service_count, endpoint_count, endpoint_url_count
        )

        password_data = {
            'username': self.user_info['username'],
            'password': self.user_info['password']
        }

        service_catalog = self.master_model.password_authenticate(
            password_data
        )
        self.check_service_catalog(
            role_count, role_names, role_data, services, service_catalog
        )

    def test_apikey_auth_failures(self):
        with self.assertRaises(exceptions.KeystoneUserError):
            apikey_data = {
                'username': '43failme',
                'apiKey': self.user_info['password']
            }
            self.master_model.apikey_authenticate(
                apikey_data
            )

        with self.assertRaises(exceptions.KeystoneUserError):
            apikey_data = {
                'username': self.user_info['username'],
                'apiKey': 9392
            }
            self.master_model.apikey_authenticate(
                apikey_data
            )

        with self.assertRaises(exceptions.KeystoneUserInvalidApiKeyError):
            apikey_data = {
                'username': self.user_info['username'],
                'apiKey': self.user_info['apikey'] + 'a'
            }
            self.master_model.apikey_authenticate(
                apikey_data
            )

        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            apikey_data = {
                'username': self.user_info['username'] + 'a',
                'apiKey': self.user_info['apikey']
            }
            self.master_model.apikey_authenticate(
                apikey_data
            )

        with self.assertRaises(exceptions.KeystoneUserInvalidApiKeyError):
            apikey_data = {
                'username': self.user_info['username'],
                'apiKey': self.user_info['apikey'] + 'a'
            }
            self.master_model.apikey_authenticate(
                apikey_data
            )

        with self.assertRaises(exceptions.KeystoneDisabledUserError):
            self.master_model.users.update_by_id(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                email=self.user_info['email'],
                password=self.user_info['password'],
                apikey=self.user_info['apikey'],
                enabled=False
            )
            apikey_data = {
                'username': self.user_info['username'],
                'apiKey': self.user_info['apikey']
            }
            self.master_model.apikey_authenticate(
                apikey_data
            )

        self.master_model.users.update_by_id(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            email=self.user_info['email'],
            password=self.user_info['password'],
            apikey=self.user_info['apikey'],
            enabled=True
        )

    @ddt.data(
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (5, 10, 3, 4),
        (2, 20, 15, 10)
    )
    @ddt.unpack
    def test_apikey_auth(
        self, role_count, service_count, endpoint_count, endpoint_url_count
    ):
        role_names, role_data = self.generate_roles(role_count)

        services = self.generate_services(
            service_count, endpoint_count, endpoint_url_count
        )

        apikey_data = {
            'username': self.user_info['username'],
            'apiKey': self.user_info['apikey']
        }

        service_catalog = self.master_model.apikey_authenticate(
            apikey_data
        )
        self.check_service_catalog(
            role_count, role_names, role_data, services, service_catalog
        )

    def test_tenant_id_token_auth_failures(self):
        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'tenantId': self.tenant_id,
                'token': {
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'tenantId': self.tenant_id
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'tenantId': 'aphrodite',
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneInvalidTokenError):
            token_data = {
                'tenantId': self.tenant_id,
                'token': {
                    'id': self.token + 'a'
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneTenantError):
            token_data = {
                'tenantId': 93920395,
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneTenantError):
            self.master_model.tenants.update_status(
                tenant_id=self.tenant_id,
                enabled=False
            )
            token_data = {
                'tenantId': self.tenant_id,
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        self.master_model.tenants.update_status(
            tenant_id=self.tenant_id,
            enabled=True
        )

        new_tenant_id = self.master_model.tenants.add(
            tenant_name='krash-kourse',
            description='breaking things',
        )
        new_user_id = self.master_model.users.add(
            tenant_id=new_tenant_id,
            username='krispy',
            email='kri@spy',
            password='$py',
            apikey='kryme',
            enabled=True
        )
        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            token_data = {
                'tenantId': new_tenant_id,
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUnknownUserError):
            self.master_model.tokens.add(
                tenant_id=new_tenant_id,
                user_id=new_user_id
            )
            token_data = {
                'tenantId': new_tenant_id,
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneDisabledUserError):
            self.master_model.users.update_by_id(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                email=self.user_info['email'],
                password=self.user_info['password'],
                apikey=self.user_info['apikey'],
                enabled=False
            )
            token_data = {
                'tenantId': self.tenant_id,
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        self.master_model.users.update_by_id(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            email=self.user_info['email'],
            password=self.user_info['password'],
            apikey=self.user_info['apikey'],
            enabled=True
        )

    @ddt.data(
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (5, 10, 3, 4),
        (2, 20, 15, 10)
    )
    @ddt.unpack
    def test_tenant_id_token_auth(
        self, role_count, service_count, endpoint_count, endpoint_url_count
    ):
        role_names, role_data = self.generate_roles(role_count)

        services = self.generate_services(
            service_count, endpoint_count, endpoint_url_count
        )

        token_data = {
            'tenantId': self.tenant_id,
            'token': {
                'id': self.token
            }
        }

        service_catalog = self.master_model.tenant_id_token_auth(
            token_data
        )
        self.check_service_catalog(
            role_count, role_names, role_data, services, service_catalog
        )

    def test_tenant_name_token_auth_failures(self):
        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'tenantName': self.tenant_info['name'],
                'token': {
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'tenantName': self.tenant_info['name']
            }
            self.master_model.tenant_id_token_auth(token_data)

        with self.assertRaises(exceptions.KeystoneUserError):
            token_data = {
                'tenantName': self.tenant_info['name'] + 'x',
                'token': {
                    'id': self.token
                }
            }
            self.master_model.tenant_id_token_auth(token_data)

    @ddt.data(
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (5, 10, 3, 4),
        (2, 20, 15, 10)
    )
    @ddt.unpack
    def test_tenant_name_token_auth(
        self, role_count, service_count, endpoint_count, endpoint_url_count
    ):
        role_names, role_data = self.generate_roles(role_count)

        services = self.generate_services(
            service_count, endpoint_count, endpoint_url_count
        )

        token_data = {
            'tenantName': self.tenant_info['name'],
            'token': {
                'id': self.token
            }
        }

        service_catalog = self.master_model.tenant_name_token_auth(
            token_data
        )
        self.check_service_catalog(
            role_count, role_names, role_data, services, service_catalog
        )
