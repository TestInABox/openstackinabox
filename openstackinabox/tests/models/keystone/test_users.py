import ddt
import six

from openstackinabox.tests.base import TestBase, DbFailure

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.db.users import KeystoneDbUsers


@ddt.ddt
class TestKeystoneDbUsers(TestBase):

    def setUp(self):
        super(TestKeystoneDbUsers, self).setUp(initialize=False)
        self.model = KeystoneDbUsers
        self.db = self.master_model.database
        from openstackinabox.models.keystone.model import KeystoneModel
        KeystoneModel.initialize_db_schema(self.master_model.database)
        self.master_model.roles.initialize()
        self.master_model.tenants.initialize()

    def tearDown(self):
        super(TestKeystoneDbUsers, self).tearDown()

    def test_initialization(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        self.assertEqual(id(self.master_model), id(instance.master))
        self.assertEqual(self.db, instance.database)
        self.assertIsNone(instance.admin_user_id)

        instance.initialize()
        self.assertIsNotNone(instance.admin_user_id)

    @ddt.data(
        0,
        1
    )
    def test_add_failure(self, row_count):
        instance = self.model(
            self.master_model,
            DbFailure(rowcount=row_count),
        )

        with self.assertRaises(exceptions.KeystoneUserError):
            instance.add(
                tenant_id=123456,
                username='Antoinette',
                email='marie@antoin.nette',
                password='ReineFinale',
                apikey='LaMortParRevolution',
                enabled=True
            )

    def test_add_and_get(self):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='overthrown',
            description='monarchs',
            enabled=True
        )

        user_info = {
            'username': 'Antoinette',
            'email': 'marie@antoin.nette',
            'password': 'ReineFinale',
            'apikey': 'LaMortParRevolution',
            'enabled': True
        }

        user_id = instance.add(
            tenant_id=tenant_id,
            username=user_info['username'],
            email=user_info['email'],
            password=user_info['password'],
            apikey=user_info['apikey'],
            enabled=user_info['enabled']
        )

        user_data = instance.get_by_id(
            tenant_id=tenant_id,
            user_id=user_id
        )
        self.assertEqual(tenant_id, user_data['tenant_id'])
        self.assertEqual(user_id, user_data['user_id'])
        self.assertEqual(user_info['username'], user_data['username'])
        self.assertEqual(user_info['email'], user_data['email'])
        self.assertEqual(user_info['password'], user_data['password'])
        self.assertEqual(user_info['apikey'], user_data['apikey'])
        self.assertEqual(user_info['enabled'], user_data['enabled'])

        username_data = instance.get_by_name(
            tenant_id=tenant_id,
            username=user_info['username']
        )
        self.assertEqual(tenant_id, username_data['tenant_id'])
        self.assertEqual(user_id, username_data['user_id'])
        self.assertEqual(user_info['username'], username_data['username'])
        self.assertEqual(user_info['email'], username_data['email'])
        self.assertEqual(user_info['password'], username_data['password'])
        self.assertEqual(user_info['apikey'], username_data['apikey'])
        self.assertEqual(user_info['enabled'], username_data['enabled'])

    def test_get_by_id_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure(),
        )

        with self.assertRaises(exceptions.KeystoneUserError):
            instance.get_by_id(
                tenant_id=123456,
                user_id=987654321
            )

    def test_get_by_name_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure(),
        )

        with self.assertRaises(exceptions.KeystoneUserError):
            instance.get_by_name(
                tenant_id=123456,
                username='Sisyphus'
            )

    @ddt.data(
        (1, 1), (1, 10), (1, 50),
        (10, 1), (10, 10), (10, 50),
        (50, 1), (50, 10), (50, 50),
    )
    @ddt.unpack
    def test_get_by_name_or_tenant_id(self, tenant_count, user_count):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        tenants = []
        users = {}
        usernames = []
        for tN in range(tenant_count):
            tid = self.master_model.tenants.add(
                tenant_name='titan_{0}'.format(tN),
                description='tenant # {0}'.format(tN),
                enabled=True
            )
            tenants.append(tid)
            users['{0}'.format(tid)] = {}

            for uN in range(user_count):

                user_info = {
                    'tenant_id': tid,
                    'username': 'Antoinette{0}'.format(uN),
                    'email': 'marie{0}@antoin.nette'.format(uN),
                    'password': 'ReineFinale{0}'.format(uN),
                    'apikey': 'LaMortParRevolution{0}'.format(uN),
                    'enabled': True
                }

                if user_info['username'] not in usernames:
                    usernames.append(user_info['username'])

                uid = instance.add(
                    tenant_id=tid,
                    username=user_info['username'],
                    email=user_info['email'],
                    password=user_info['password'],
                    apikey=user_info['apikey'],
                    enabled=user_info['enabled']
                )

                user_info['user_id'] = uid
                users['{0}'.format(tid)]['{0}'.format(uid)] = user_info

        for tid in tenants:
            tenant_users = [
                tenant_user_data
                for tenant_user_data in instance.get_by_name_or_tenant_id(
                    tenant_id=tid
                )
            ]
            self.assertEqual(len(tenant_users), user_count)

            for tenant_user_data in tenant_users:
                self.assertIn(
                    '{0}'.format(tenant_user_data['tenant_id']),
                    users
                )
                self.assertIn(
                    '{0}'.format(tenant_user_data['user_id']),
                    users['{0}'.format(tenant_user_data['tenant_id'])]
                )
                for k, v in six.iteritems(
                    users[
                        '{0}'.format(tenant_user_data['tenant_id'])
                    ][
                        '{0}'.format(tenant_user_data['user_id'])
                    ]
                ):
                    self.assertIn(k, tenant_user_data)
                    self.assertEqual(v, tenant_user_data[k])

        for username in usernames:
            username_users = [
                username_user_data
                for username_user_data in instance.get_by_name_or_tenant_id(
                    username=username
                )
            ]
            self.assertEqual(len(username_users), tenant_count)

            for username_user_data in username_users:
                self.assertIn(
                    '{0}'.format(username_user_data['tenant_id']),
                    users
                )
                self.assertIn(
                    '{0}'.format(username_user_data['user_id']),
                    users['{0}'.format(username_user_data['tenant_id'])]
                )
                for k, v in six.iteritems(
                    users[
                        '{0}'.format(username_user_data['tenant_id'])
                    ][
                        '{0}'.format(username_user_data['user_id'])
                    ]
                ):
                    self.assertIn(k, username_user_data)
                    self.assertEqual(v, username_user_data[k])

    def test_update_by_id_failure(self):
        instance = self.model(
            self.master_model,
            DbFailure(),
        )

        with self.assertRaises(exceptions.KeystoneUserError):
            instance.update_by_id(
                tenant_id=123456,
                user_id=987654321,
                email='marie@antoin.nette',
                password='ReineFinale',
                apikey='LaMortParRevolution',
                enabled=True
            )

    @ddt.data(
        (None, None, None, None)
    )
    @ddt.unpack
    def test_update_by_id(self, new_enabled, new_email, new_password,
                          new_apikey):
        instance = self.model(
            self.master_model,
            self.db
        )

        tenant_id = self.master_model.tenants.add(
            tenant_name='overthrown',
            description='monarchs',
            enabled=True
        )

        user_info = {
            'username': 'Antoinette',
            'email': 'marie@antoin.nette',
            'password': 'ReineFinale',
            'apikey': 'LaMortParRevolution',
            'enabled': True
        }

        user_id = instance.add(
            tenant_id=tenant_id,
            username=user_info['username'],
            email=user_info['email'],
            password=user_info['password'],
            apikey=user_info['apikey'],
            enabled=user_info['enabled']
        )

        new_user_info = {
            'tenant_id': tenant_id,
            'user_id': user_id,

            'email': (
                user_info['email']
                if new_email is None else new_email
            ),
            'password': (
                user_info['password']
                if new_password is None else new_password
            ),
            'apikey': (
                user_info['apikey']
                if new_apikey is None else new_apikey
            ),
            'enabled': (
                user_info['enabled']
                if new_enabled is None
                else new_enabled
            )
        }

        instance.update_by_id(**new_user_info)

        user_data = instance.get_by_id(
            tenant_id=tenant_id,
            user_id=user_id
        )
        self.assertEqual(tenant_id, user_data['tenant_id'])
        self.assertEqual(user_id, user_data['user_id'])
        self.assertEqual(new_user_info['email'], user_data['email'])
        self.assertEqual(new_user_info['password'], user_data['password'])
        self.assertEqual(new_user_info['apikey'], user_data['apikey'])
        self.assertEqual(new_user_info['enabled'], user_data['enabled'])

    @ddt.data(
        (1, 1), (1, 10), (1, 50),
        # (10, 1), (10, 10), (10, 50),
        # (50, 1), (50, 10), (50, 50),
    )
    @ddt.unpack
    def test_get_for_tenant_id(self, tenant_count, user_count):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        tenants = []
        users = {}
        for tN in range(tenant_count):
            tid = self.master_model.tenants.add(
                tenant_name='titan_{0}'.format(tN),
                description='tenant # {0}'.format(tN),
                enabled=True
            )
            tenants.append(tid)
            users['{0}'.format(tid)] = {}

            for uN in range(user_count):

                user_info = {
                    'tenant_id': tid,
                    'username': 'Antoinette{0}'.format(uN),
                    'email': 'marie{0}@antoin.nette'.format(uN),
                    'password': 'ReineFinale{0}'.format(uN),
                    'apikey': 'LaMortParRevolution{0}'.format(uN),
                    'enabled': True
                }

                uid = instance.add(
                    tenant_id=tid,
                    username=user_info['username'],
                    email=user_info['email'],
                    password=user_info['password'],
                    apikey=user_info['apikey'],
                    enabled=user_info['enabled']
                )

                user_info['user_id'] = uid
                users['{0}'.format(tid)]['{0}'.format(uid)] = user_info

        for tid in tenants:
            tenant_users = [
                tenant_user_data
                for tenant_user_data in instance.get_for_tenant_id(
                    tenant_id=tid
                )
            ]
            self.assertEqual(len(tenant_users), user_count)

            for tenant_user_data in tenant_users:
                self.assertIn(
                    '{0}'.format(tenant_user_data['tenant_id']),
                    users
                )
                self.assertIn(
                    '{0}'.format(tenant_user_data['user_id']),
                    users['{0}'.format(tenant_user_data['tenant_id'])]
                )
                for k, v in six.iteritems(
                    users[
                        '{0}'.format(tenant_user_data['tenant_id'])
                    ][
                        '{0}'.format(tenant_user_data['user_id'])
                    ]
                ):
                    self.assertIn(k, tenant_user_data)
                    self.assertEqual(v, tenant_user_data[k])
