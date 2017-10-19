import sqlite3

import ddt
import mock

from openstackinabox.tests.base import TestBase

from openstackinabox.models.swift import exceptions
from openstackinabox.models.swift import model


@ddt.ddt
class TestSwiftModel(TestBase):

    def setUp(self):
        super(TestSwiftModel, self).setUp(initialize=False)
        self.tenant_id = '123456'
        self.tenant_path = '/{0}'.format(self.tenant_id)
        self.container_name = 'foobar'
        self.container_path = '{0}/{1}'.format(
            self.tenant_path,
            self.container_name
        )
        self.object_name = 'raboof'
        self.object_path = '{0}/{1}'.format(
            self.container_path,
            self.object_name
        )

    def tearDown(self):
        super(TestSwiftModel, self).tearDown()

    def test_initialize_db_schema(self):
        db_cursor = mock.MagicMock()
        db_execute = mock.MagicMock()
        db_commit = mock.MagicMock()
        db_instance = mock.MagicMock()
        db_instance.cursor.return_value = db_cursor
        db_instance.commit = db_commit
        db_cursor.execute = db_execute

        model.SwiftServiceModel.initialize_db_schema(db_instance)
        self.assertTrue(db_instance.cursor.called)
        self.assertTrue(db_execute.called)
        self.assertTrue(db_commit.called)
        self.assertEqual(db_execute.call_count, len(model.schema))
        for s in model.schema:
            db_execute.assert_any_call(s)

    @ddt.data(
        False,
        True
    )
    def test_initialize(self, auto_initialize):
        instance = model.SwiftServiceModel(initialize=auto_initialize)

        if not auto_initialize:
            # error raised if we try to put anything into the database
            with self.assertRaises(sqlite3.OperationalError):
                instance.add_tenant(self.tenant_id, self.tenant_path)
        else:
            # put something into each table
            internal_tenant_id = instance.add_tenant(
                self.tenant_id,
                self.tenant_path
            )

            internal_container_id = instance.add_container(
                internal_tenant_id,
                self.container_name,
                self.container_path
            )

            instance.add_object(
                internal_tenant_id,
                internal_container_id,
                self.object_name,
                self.object_path
            )

            self.assertTrue(
                instance.has_tenant(
                    self.tenant_id
                )
            )
            self.assertTrue(
                instance.has_container(
                    internal_tenant_id,
                    self.container_name
                )
            )
            self.assertTrue(
                instance.has_object(
                    internal_tenant_id,
                    internal_container_id,
                    self.object_name
                )
            )

    def test_database(self):
        instance = model.SwiftServiceModel()
        self.assertIsInstance(instance.database, sqlite3.Connection)

    @ddt.data(
        'has', 'get'
    )
    def test_tenant_failure(self, method):
        instance = model.SwiftServiceModel()

        with self.assertRaises(exceptions.SwiftUnknownTenantError):
            if method == 'has':
                instance.has_tenant(self.tenant_id)
            elif method == 'get':
                instance.get_tenant(123456)

    def test_tenant_success(self):
        instance = model.SwiftServiceModel()

        internal_tenant_id = instance.add_tenant(
            self.tenant_id,
            self.tenant_path
        )
        self.assertEqual(
            instance.has_tenant(self.tenant_id),
            internal_tenant_id
        )

        tenant_data = instance.get_tenant(internal_tenant_id)
        self.assertEqual(
            tenant_data['id'],
            internal_tenant_id
        )
        self.assertEqual(
            tenant_data['tenantid'],
            self.tenant_id
        )
        self.assertEqual(
            tenant_data['path'],
            self.tenant_path
        )

    @ddt.data(
        'has', 'get'
    )
    def test_container_failure(self, method):
        instance = model.SwiftServiceModel()
        internal_tenant_id = instance.add_tenant(
            self.tenant_id,
            self.tenant_path
        )

        with self.assertRaises(exceptions.SwiftUnknownContainerError):
            if method == 'has':
                instance.has_container(internal_tenant_id, self.container_name)
            elif method == 'get':
                instance.get_container(internal_tenant_id, 123456)

    def test_container_success(self):
        instance = model.SwiftServiceModel()
        internal_tenant_id = instance.add_tenant(
            self.tenant_id,
            self.tenant_path
        )

        internal_container_id = instance.add_container(
            internal_tenant_id,
            self.container_name,
            self.container_path
        )

        self.assertEqual(
            instance.has_container(
                internal_tenant_id,
                self.container_name
            ),
            internal_container_id
        )

        container_data = instance.get_container(
            internal_tenant_id,
            internal_container_id
        )
        self.assertEqual(
            container_data['tenantid'],
            internal_tenant_id
        )
        self.assertEqual(
            container_data['containerid'],
            internal_container_id
        )
        self.assertEqual(
            container_data['container_name'],
            self.container_name
        )
        self.assertEqual(
            container_data['path'],
            self.container_path
        )

    @ddt.data(
        'has', 'get'
    )
    def test_object_failure(self, method):
        instance = model.SwiftServiceModel()
        internal_tenant_id = instance.add_tenant(
            self.tenant_id,
            self.tenant_path
        )
        internal_container_id = instance.add_container(
            internal_tenant_id,
            self.container_name,
            self.container_path
        )

        with self.assertRaises(exceptions.SwiftUnknownObjectError):
            if method == 'has':
                instance.has_object(
                    internal_tenant_id,
                    internal_container_id,
                    self.object_name
                )
            elif method == 'get':
                instance.get_object(
                    internal_tenant_id,
                    internal_container_id,
                    123456
                )

    def test_object_success(self):
        instance = model.SwiftServiceModel()
        internal_tenant_id = instance.add_tenant(
            self.tenant_id,
            self.tenant_path
        )
        internal_container_id = instance.add_container(
            internal_tenant_id,
            self.container_name,
            self.container_path
        )

        internal_object_id = instance.add_object(
            internal_tenant_id,
            internal_container_id,
            self.object_name,
            self.object_path
        )

        self.assertEqual(
            instance.has_object(
                internal_tenant_id,
                internal_container_id,
                self.object_name
            ),
            internal_object_id
        )

        object_data = instance.get_object(
            internal_tenant_id,
            internal_container_id,
            internal_object_id
        )
        self.assertEqual(
            object_data['tenantid'],
            internal_tenant_id
        )
        self.assertEqual(
            object_data['containerid'],
            internal_container_id
        )
        self.assertEqual(
            object_data['objectid'],
            internal_object_id
        )
        self.assertEqual(
            object_data['object_name'],
            self.object_name
        )
        self.assertEqual(
            object_data['path'],
            self.object_path
        )

    def test_remove_object(self):
        instance = model.SwiftServiceModel()
        internal_tenant_id = instance.add_tenant(
            self.tenant_id,
            self.tenant_path
        )
        internal_container_id = instance.add_container(
            internal_tenant_id,
            self.container_name,
            self.container_path
        )

        internal_object_id = instance.add_object(
            internal_tenant_id,
            internal_container_id,
            self.object_name,
            self.object_path
        )

        self.assertEqual(
            instance.has_object(
                internal_tenant_id,
                internal_container_id,
                self.object_name
            ),
            internal_object_id
        )

        instance.remove_object(
            internal_tenant_id,
            internal_container_id,
            internal_object_id
        )

        with self.assertRaises(exceptions.SwiftUnknownObjectError):
            instance.has_object(
                internal_tenant_id,
                internal_container_id,
                self.object_name
            )
