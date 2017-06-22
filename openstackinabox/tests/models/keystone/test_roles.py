import uuid

import ddt

from openstackinabox.tests.base import TestBase, DbFailure

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.db.roles import KeystoneDbRoles


@ddt.ddt
class TestKeystoneDbRoles(TestBase):

    def setUp(self):
        super(TestKeystoneDbRoles, self).setUp()
        self.model = KeystoneDbRoles
        self.master = 'Venus'
        self.db = self.get_testing_database()

        self.role_info = {
            'name': 'role_{0}'.format(
                str(uuid.uuid4())
            )
        }

    def tearDown(self):
        super(TestKeystoneDbRoles, self).tearDown()

    def test_initialization(self):
        instance = self.model(
            self.master,
            self.db
        )
        self.assertEqual(self.master, instance.master)
        self.assertEqual(self.db, instance.database)
        self.assertIsNone(instance.admin_role_id)
        self.assertIsNone(instance.viewer_role_id)

        instance.initialize()
        self.assertIsNotNone(instance.admin_role_id)
        self.assertIsNotNone(instance.viewer_role_id)

    def test_add_failure(self):
        instance = self.model(
            self.master,
            DbFailure(),
        )
        with self.assertRaises(exceptions.KeystoneRoleError):
            instance.add('br34k1ng4llth1ng$')

    def test_add_user_role_by_id_failure(self):
        instance = self.model(
            self.master,
            DbFailure(),
        )
        with self.assertRaises(exceptions.KeystoneRoleError):
            instance.add_user_role_by_id(
                tenant_id=0,
                user_id=0,
                role_id=1
            )

    def test_add_and_get(self):
        instance = self.model(
            self.master,
            self.db
        )
        instance.initialize()

        with self.assertRaises(exceptions.KeystoneRoleError):
            instance.get(
                self.role_info['name']
            )

        role_id = instance.add(
            self.role_info['name']
        )
        role_data = instance.get(
            self.role_info['name']
        )
        self.assertEqual(
            role_id,
            role_data['id']
        )
        self.assertEqual(
            self.role_info['name'],
            role_data['name']
        )

    @ddt.data(
        'tenant',
        'user',
        'role',
        None
    )
    def test_add_user_role_by_id(self, invalid_value):
        role_name = 'phearB0t'
        tenant = {
            'name': 'megaTokyo',
            'description': 'US Manga'
        }
        user = {
            'name': 'largo',
            'email': 'l4rg0@ph34rm3.n3t',
            'password': '3l1t30n3$rul3',
            'apikey': 'p4$$w0rd$suck'
        }

        tenant_id = self.tenants.add(
            tenant_name=tenant['name'],
            description=tenant['description'],
            enabled=True
        )

        user_id = self.users.add(
            tenant_id=tenant_id,
            username=user['name'],
            email=user['email'],
            password=user['password'],
            apikey=user['apikey'],
            enabled=True
        )

        role_id = self.roles.add(
            role_name
        )

        if invalid_value is None:
            self.roles.add_user_role_by_id(
                tenant_id=tenant_id,
                user_id=user_id,
                role_id=role_id,
            )

            user_roles = self.roles.get_user_roles(
                tenant_id=tenant_id,
                user_id=user_id,
            )

            self.assertEqual(1, len(user_roles))
            for user_role in user_roles:
                self.assertEqual(role_id, user_role['id'])
                self.assertEqual(role_name, user_role['name'])
        else:
            with self.assertRaises(exceptions.KeystoneRoleError):
                self.roles.add_user_role_by_id(
                    tenant_id=tenant_id if invalid_value != 'tenant' else None,
                    user_id=user_id if invalid_value != 'user' else None,
                    role_id=role_id if invalid_value != 'role' else None
                )

    def test_add_user_role_by_name(self):
        role_name = 'phearB0t'
        tenant = {
            'name': 'megaTokyo',
            'description': 'US Manga'
        }
        user = {
            'name': 'largo',
            'email': 'l4rg0@ph34rm3.n3t',
            'password': '3l1t30n3$rul3',
            'apikey': 'p4$$w0rd$suck'
        }

        tenant_id = self.tenants.add(
            tenant_name=tenant['name'],
            description=tenant['description'],
            enabled=True
        )
        user_id = self.users.add(
            tenant_id=tenant_id,
            username=user['name'],
            email=user['email'],
            password=user['password'],
            apikey=user['apikey'],
            enabled=True
        )
        role_id = self.roles.add(
            role_name
        )

        self.roles.add_user_role_by_role_name(
            tenant_id=tenant_id,
            user_id=user_id,
            role_name=role_name
        )

        user_roles = self.roles.get_user_roles(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        self.assertEqual(1, len(user_roles))
        for user_role in user_roles:
            self.assertEqual(role_id, user_role['id'])
            self.assertEqual(role_name, user_role['name'])

    @ddt.data(
        0,
        1,
        20
    )
    def test_get_user_roles(self, role_count):
        tenant = {
            'name': 'megaTokyo',
            'description': 'US Manga'
        }
        user = {
            'name': 'largo',
            'email': 'l4rg0@ph34rm3.n3t',
            'password': '3l1t30n3$rul3',
            'apikey': 'p4$$w0rd$suck'
        }

        tenant_id = self.tenants.add(
            tenant_name=tenant['name'],
            description=tenant['description'],
            enabled=True
        )
        user_id = self.users.add(
            tenant_id=tenant_id,
            username=user['name'],
            email=user['email'],
            password=user['password'],
            apikey=user['apikey'],
            enabled=True
        )

        role_names = [
            'ph34rb0t_{0}'.format(x)
            for x in range(role_count)
        ]

        roles = [
            {
                'name': name,
                'id': self.roles.add(name)
            }
            for name in role_names
        ]

        for role in roles:
            self.roles.add_user_role_by_id(
                tenant_id=tenant_id,
                user_id=user_id,
                role_id=role['id']
            )

        user_roles = self.roles.get_user_roles(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        self.assertEqual(role_count, len(user_roles))

        def find_index(rolename):
            for x in range(len(roles)):
                if roles[x]['name'] == rolename:
                    return x

            return None

        for user_role in user_roles:
            role_index = find_index(user_role['name'])
            self.assertIsNotNone(role_index)

            role_info = roles[role_index]
            self.assertEqual(role_info['id'], user_role['id'])
            self.assertEqual(role_info['name'], user_role['name'])
