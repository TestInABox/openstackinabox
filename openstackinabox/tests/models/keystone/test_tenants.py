import ddt

from openstackinabox.tests.base import TestBase, DbFailure

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.db.tenants import KeystoneDbTenants


@ddt.ddt
class TestKeystoneDbTenants(TestBase):

    def setUp(self):
        super(TestKeystoneDbTenants, self).setUp()
        self.model = KeystoneDbTenants
        self.master = 'Mercury'
        self.db = self.get_testing_database()

    def tearDown(self):
        super(TestKeystoneDbTenants, self).tearDown()

    def test_initialization(self):
        instance = self.model(
            self.master,
            self.db
        )
        self.assertEqual(self.master, instance.master)
        self.assertEqual(self.db, instance.database)
        self.assertIsNone(instance.admin_tenant_id)

        instance.initialize()
        self.assertIsNotNone(instance.admin_tenant_id)

    @ddt.data(
        0,
        1
    )
    def test_add_failure(self, row_count):
        instance = self.model(
            self.master,
            DbFailure(rowcount=row_count),
        )
        with self.assertRaises(exceptions.KeystoneTenantError):
            instance.add(
                tenant_name='Saturn',
                description='Planetary Bodice',
                enabled=True
            )

    def test_add_and_get(self):
        instance = self.model(
            self.master,
            self.db
        )
        instance.initialize()

        tenant_info = {
            'name': 'Pluto',
            'description': 'False Planet',
            'enabled': True
        }
        tenant_id = instance.add(
            tenant_name=tenant_info['name'],
            description=tenant_info['description'],
            enabled=tenant_info['enabled']
        )

        tenant_data = instance.get_by_id(tenant_id)
        self.assertEqual(tenant_id, tenant_data['id'])
        self.assertEqual(tenant_info['name'], tenant_data['name'])
        self.assertEqual(
            tenant_info['description'],
            tenant_data['description']
        )
        self.assertEqual(tenant_info['enabled'], tenant_data['enabled'])

    def test_get_by_id_failure(self):
        instance = self.model(
            self.master,
            self.db
        )
        instance.initialize()
        with self.assertRaises(exceptions.KeystoneTenantError):
            instance.get_by_id(192)

    @ddt.data(
        0,
        1,
        50
    )
    def test_get_by_id(self, tenant_count):
        instance = self.model(
            self.master,
            self.db
        )
        instance.initialize()

        tenants = [
            {
                'name': 'Plato{0}'.format(x),
                'description': 'tenant {0}'.format(x),
                'enabled': True
            }
            for x in range(tenant_count)
        ]

        tenant_ids = [
            instance.add(
                tenant_name=tenant['name'],
                description=tenant['description'],
                enabled=tenant['enabled']
            )
            for tenant in tenants
        ]

        stored_tenants = instance.get()

        # -1 since the 'admin' tenant is part of the base model
        self.assertEqual(len(stored_tenants) - 1, len(tenant_ids))
        for stored_tenant in stored_tenants:
            if stored_tenant['id'] != 1:
                self.assertIn(stored_tenant['id'], tenant_ids)
                found = False
                for tenant in tenants:
                    if tenant['name'] == stored_tenant['name']:
                        self.assertEqual(
                            tenant['description'],
                            stored_tenant['description']
                        )
                        self.assertEqual(
                            tenant['enabled'],
                            stored_tenant['enabled']
                        )
                        found = True
                self.assertTrue(found)

    @ddt.data(
        True,
        False
    )
    def test_update_description(self, is_valid):
        instance = self.model(
            self.master,
            self.db
        )
        instance.initialize()

        tenant_info = {
            'name': 'Pluto',
            'description': 'False Planet',
            'enabled': True
        }
        tenant_id = instance.add(
            tenant_name=tenant_info['name'],
            description=tenant_info['description'],
            enabled=tenant_info['enabled']
        ) if is_valid else 0

        if is_valid:
            old_tenant_info = instance.get_by_id(
                tenant_id
            )
            self.assertEqual(
                old_tenant_info['description'],
                tenant_info['description']
            )

            new_description = "wisdom ignores fools"

            instance.update_description(
                tenant_id=tenant_id,
                description=new_description
            )

            updated_tenant_info = instance.get_by_id(
                tenant_id
            )
            self.assertEqual(
                updated_tenant_info['description'],
                new_description
            )

        else:
            with self.assertRaises(exceptions.KeystoneTenantError):
                instance.update_description(
                    tenant_id=tenant_id,
                    description="foolishness abides fools"
                )

    @ddt.data(
        True,
        False
    )
    def test_update_status(self, is_valid):
        instance = self.model(
            self.master,
            self.db
        )
        instance.initialize()

        tenant_info = {
            'name': 'Pluto',
            'description': 'False Planet',
            'enabled': True
        }
        tenant_id = instance.add(
            tenant_name=tenant_info['name'],
            description=tenant_info['description'],
            enabled=tenant_info['enabled']
        ) if is_valid else 0

        if is_valid:
            old_tenant_info = instance.get_by_id(
                tenant_id
            )
            self.assertTrue(
                old_tenant_info['enabled']
            )

            instance.update_status(
                tenant_id=tenant_id,
                enabled=False
            )

            updated_tenant_info = instance.get_by_id(
                tenant_id
            )
            self.assertFalse(
                updated_tenant_info['enabled']
            )

        else:
            with self.assertRaises(exceptions.KeystoneTenantError):
                instance.update_status(
                    tenant_id=tenant_id,
                    enabled=False
                )
