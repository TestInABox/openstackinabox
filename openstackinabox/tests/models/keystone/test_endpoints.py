import ddt
import six

from openstackinabox.tests.base import TestBase, DbFailure

from openstackinabox.models.keystone import exceptions
from openstackinabox.models.keystone.db.endpoints import (
    KeystoneDbServiceEndpoints
)


@ddt.ddt
class TestKeystoneDbEndpoints(TestBase):

    def setUp(self):
        super(TestKeystoneDbEndpoints, self).setUp()
        self.model = KeystoneDbServiceEndpoints
        self.master = 'Pluto'
        self.db = self.master_model.database
        self.master_model.services.initialize()

    def tearDown(self):
        super(TestKeystoneDbEndpoints, self).tearDown()

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
        with self.assertRaises(
            exceptions.KeystoneServiceCatalogEndpointError
        ):
            instance.add(
                90210,
                'nullspace',
                'version.info',
                'version.list',
                '101101101'
            )

    @staticmethod
    def get_endpoints(instance, service_id, endpoint_id):
        many = [
            endpoint
            for endpoint in instance.get(service_id)
        ]

        one = [
            endpoint
            for endpoint in instance.get(service_id, endpoint_id=endpoint_id)
        ]

        return (many, one)

    def test_add_and_get(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        service_id = self.master_model.services.add(
            '/dev/null',
            'void'
        )

        empty_many, empty_one = self.get_endpoints(
            instance,
            service_id,
            12345
        )
        self.assertEqual(0, len(empty_many))
        self.assertEqual(0, len(empty_one))

        endpoint_info = {
            'region': 'nullspace',
            'version_info': 'info.ver',
            'version_list': 'list.ver',
            'version_id': '1101'
        }

        endpoint_id = instance.add(
            service_id,
            endpoint_info['region'],
            endpoint_info['version_info'],
            endpoint_info['version_list'],
            endpoint_info['version_id'],
        )

        data_many, data_one = self.get_endpoints(
            instance,
            service_id,
            endpoint_id
        )

        self.assertEqual(1, len(data_one))
        endpoint_data = data_one[0]
        self.assertEqual(service_id, endpoint_data['service_id'])
        for k, v in six.iteritems(endpoint_info):
            self.assertIn(k, endpoint_data)
            self.assertEqual(v, endpoint_data[k])

        self.assertEqual(1, len(data_many))
        full_endpoint_data = data_many[0]
        self.assertEqual(service_id, full_endpoint_data['service_id'])
        for k, v in six.iteritems(endpoint_info):
            self.assertIn(k, full_endpoint_data)
            self.assertEqual(v, full_endpoint_data[k])

    def test_delete_failure(self):
        instance = self.model(
            self.master,
            DbFailure(),
        )
        with self.assertRaises(
            exceptions.KeystoneServiceCatalogEndpointError
        ):
            instance.delete(
                90210,
                12345
            )

    def test_add_delete_get(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        service_id = self.master_model.services.add(
            '/dev/null',
            'void'
        )

        empty_many, empty_one = self.get_endpoints(
            instance,
            service_id,
            12345
        )
        self.assertEqual(0, len(empty_many))
        self.assertEqual(0, len(empty_one))

        endpoint_info = {
            'region': 'nullspace',
            'version_info': 'info.ver',
            'version_list': 'list.ver',
            'version_id': '1101'
        }

        endpoint_id = instance.add(
            service_id,
            endpoint_info['region'],
            endpoint_info['version_info'],
            endpoint_info['version_list'],
            endpoint_info['version_id'],
        )

        data_many, data_one = self.get_endpoints(
            instance,
            service_id,
            endpoint_id
        )
        self.assertEqual(1, len(data_one))
        self.assertEqual(1, len(data_many))

        instance.delete(service_id, endpoint_id)

        deleted_many, deleted_one = self.get_endpoints(
            instance,
            service_id,
            endpoint_id
        )
        self.assertEqual(0, len(deleted_one))
        self.assertEqual(0, len(deleted_many))

    @ddt.data(
        0,
        1
    )
    def test_add_url_failure(self, row_count):
        instance = self.model(
            self.master,
            DbFailure(rowcount=row_count),
        )
        with self.assertRaises(
            exceptions.KeystoneServiceCatalogEndpointError
        ):
            instance.add_url(
                12345,
                'mock',
                'url.mock'
            )

    @staticmethod
    def get_endpoint_urls(instance, endpoint_id, url_id):
        many = [
            url
            for url in instance.get_url(endpoint_id)
        ]

        one = [
            url
            for url in instance.get_url(endpoint_id, url_id=url_id)
        ]

        return (many, one)

    def test_add_and_get_url(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        service_id = self.master_model.services.add(
            '/dev/null',
            'void'
        )

        endpoint_id = instance.add(
            service_id,
            'nullspace',
            'info.ver',
            'list.ver',
            '1101',
        )

        empty_many, empty_one = self.get_endpoint_urls(
            instance,
            endpoint_id,
            39495
        )
        self.assertEqual(0, len(empty_many))
        self.assertEqual(0, len(empty_one))

        url_info = {
            'name': 'trident',
            'url': 'fork.road'
        }

        url_id = instance.add_url(
            endpoint_id,
            url_info['name'],
            url_info['url']
        )

        data_many, data_one = self.get_endpoint_urls(
            instance,
            endpoint_id,
            url_id
        )
        self.assertEqual(1, len(data_many))
        url_data_many = data_many[0]
        self.assertEqual(endpoint_id, url_data_many['endpoint_id'])
        for k, v in six.iteritems(url_info):
            self.assertIn(k, url_data_many)
            self.assertEqual(v, url_data_many[k])

        self.assertEqual(1, len(data_one))
        url_data_one = data_one[0]
        self.assertEqual(endpoint_id, url_data_one['endpoint_id'])
        for k, v in six.iteritems(url_info):
            self.assertIn(k, url_data_one)
            self.assertEqual(v, url_data_one[k])

    def test_delete_url_failure(self):
        instance = self.model(
            self.master,
            DbFailure(),
        )
        with self.assertRaises(
            exceptions.KeystoneEndpointUrlError
        ):
            instance.delete_url(
                'mock',
                'url.mock'
            )

    def test_add_delete_get_url(self):
        instance = self.model(
            self.master_model,
            self.db
        )
        instance.initialize()

        service_id = self.master_model.services.add(
            '/dev/null',
            'void'
        )

        endpoint_id = instance.add(
            service_id,
            'nullspace',
            'info.ver',
            'list.ver',
            '1101',
        )

        empty_many, empty_one = self.get_endpoint_urls(
            instance,
            endpoint_id,
            39495
        )
        self.assertEqual(0, len(empty_many))
        self.assertEqual(0, len(empty_one))

        url_info = {
            'name': 'trident',
            'url': 'fork.road'
        }

        url_id = instance.add_url(
            endpoint_id,
            url_info['name'],
            url_info['url']
        )

        data_many, data_one = self.get_endpoint_urls(
            instance,
            endpoint_id,
            url_id
        )
        self.assertEqual(1, len(data_many))
        self.assertEqual(1, len(data_one))

        instance.delete_url(endpoint_id, url_id)

        deleted_many, deleted_one = self.get_endpoint_urls(
            instance,
            endpoint_id,
            url_id
        )
        self.assertEqual(0, len(deleted_many))
        self.assertEqual(0, len(deleted_one))
