import ddt
import six

from openstackinabox.tests.base import TestBase, DbFailure

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.db.services import (
    KeystoneDbServices
)


@ddt.ddt
class TestKeystoneDbServices(TestBase):

    def setUp(self):
        super(TestKeystoneDbServices, self).setUp()
        self.model = KeystoneDbServices
        self.master = 'Pluto'
        self.db = self.master_model.database

    def tearDown(self):
        super(TestKeystoneDbServices, self).tearDown()

    def test_initialization(self):
        instance = self.model(
            self.master,
            self.db
        )
        self.assertEqual(self.master, instance.master)
        self.assertEqual(self.db, instance.database)

        instance.initialize()

    @ddt.data(
        0,
        1
    )
    def test_add_failure(self, row_count):
        instance = self.model(
            self.master,
            DbFailure(rowcount=row_count),
        )
        instance.initialize()
        with self.assertRaises(
            exceptions.KeystoneServiceCatalogServiceError
        ):
            instance.add(
                'whoopie',
                'making'
            )

    @staticmethod
    def get_services(instance, service_id):
        many = [
            service
            for service in instance.get()
        ]

        one = [
            service
            for service in instance.get(service_id=service_id)
        ]

        return (many, one)

    def test_add_and_get(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        empty_many, empty_one = self.get_services(
            instance,
            929395
        )

        service_info = {
            'name': 'periodic',
            'type': 'table'
        }

        service_id = instance.add(
            service_info['name'],
            service_info['type']
        )

        data_many, data_one = self.get_services(
            instance,
            service_id
        )

        self.assertEqual(1, len(data_many))

        full_services = data_many[0]
        self.assertEqual(service_id, full_services['id'])
        for k, v in six.iteritems(service_info):
            self.assertIn(k, full_services)
            self.assertEqual(v, full_services[k])

        self.assertEqual(1, len(data_one))
        service_data = data_one[0]
        self.assertEqual(service_id, service_data['id'])
        for k, v in six.iteritems(service_info):
            self.assertIn(k, service_data)
            self.assertEqual(v, service_data[k])

    def test_delete_failure(self):
        instance = self.model(
            self.master,
            DbFailure(),
        )
        instance.initialize()
        with self.assertRaises(
            exceptions.KeystoneServiceCatalogServiceError
        ):
            instance.delete('mock')

    def test_add_delete_get(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        empty_many, empty_one = self.get_services(
            instance,
            929395
        )

        service_info = {
            'name': 'periodic',
            'type': 'table'
        }

        service_id = instance.add(
            service_info['name'],
            service_info['type']
        )

        data_many, data_one = self.get_services(
            instance,
            service_id
        )
        self.assertEqual(1, len(data_many))
        self.assertEqual(1, len(data_one))

        instance.delete(service_id)

        delete_many, delete_one = self.get_services(
            instance,
            service_id
        )
        self.assertEqual(0, len(delete_many))
        self.assertEqual(0, len(delete_one))
