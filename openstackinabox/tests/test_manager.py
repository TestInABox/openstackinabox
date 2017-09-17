"""
"""
import unittest

import ddt
import mock

from openstackinabox import manager
from openstackinabox.services import keystone


class ExampleService(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def name(self):
        return 'example-service'


@ddt.ddt
class TestOpenStackServicesManager(unittest.TestCase):

    def setUp(self):
        super(TestOpenStackServicesManager, self).setUp()

    def tearDown(self):
        super(TestOpenStackServicesManager, self).tearDown()

    def test_instantiation_basic(self):
        m = manager.OpenStackServicesManager()
        self.assertIsNone(m._keystone_service)
        self.assertIsNone(m._identity_url)
        self.assertEqual('localhost', m.base_url)
        self.assertEqual(len(m._available_regions), 1)
        self.assertIn('mock', m._available_regions)
        self.assertEqual(len(m._active_services), 0)

        with self.assertRaises(manager.ServiceNotAvailable):
            m.keystone_service

        with self.assertRaises(manager.KeystoneUrlNotSet):
            m.identity_url

    def test_base_url_setter(self):
        m = manager.OpenStackServicesManager()
        self.assertEqual('localhost', m.base_url)
        m.base_url = 'howdy'
        self.assertEqual('howdy', m.base_url)

    def test_get_keystone_service(self):
        m = manager.OpenStackServicesManager()
        m.activate_service('Keystone', 'v2', ['mock'])
        self.assertIsNone(m._keystone_service)
        keystone_service = m.keystone_service
        self.assertIsInstance(keystone_service, keystone.KeystoneV2Service)
        self.assertEqual(id(keystone_service), id(m.keystone_service))

    def test_identity_url_not_set(self):
        m = manager.OpenStackServicesManager()
        with self.assertRaises(manager.KeystoneUrlNotSet):
            m.identity_url

    def test_identity_url(self):
        base_url = 'localhost'
        m = manager.OpenStackServicesManager()
        m.base_url = base_url
        m.activate_service('Keystone', 'v2', ['mock'])
        m.create_service_catalog()
        self.assertEqual(
            m.identity_url,
            m._identity_url_template.format(base_url)
        )

    @ddt.data(
        {},
        {'HelloWorld': {}},
        {'HelloWorld': {'v1': {}}},
    )
    def test_get_service_failure(self, active_services):
        m = manager.OpenStackServicesManager()
        m._active_services = active_services
        with self.assertRaises(manager.ServiceNotAvailable):
            m.get_service('HelloWorld', 'v1')

    def test_get_service_success(self):
        sample = ExampleService()

        m = manager.OpenStackServicesManager()
        m._active_services = {
            'HelloWorld': {
                'v1': {
                    'instance': sample
                }
            }
        }

        self.assertEqual(
            sample,
            m.get_service('HelloWorld', 'v1')
        )

    @ddt.data(
        ({}, False, (), {}),
        ({'HelloWorld': {}}, False, (), {}),
        ({'HelloWorld': {'v1': {}}}, False, (), {}),
        ({'HelloWorld': {
            'v1': {'instance': ExampleService(), 'registrations': []}}},
         False, (), {}),
    )
    @ddt.unpack
    def test_add_service(
        self, active_services, has_service, service_args, service_kwargs
    ):

        m = manager.OpenStackServicesManager()
        m._active_services = active_services

        service_data = {
            'service': ExampleService,
            'access': {
                'in_service_catalog': False,
                'keystone_service': None,
            },
            'entries': [
                {
                    'version': 1,
                    'type': 'example',
                    'name': 'my example service',
                    'urls': {
                        'public': 'https://{0}/example/v1/'
                    }
                }
            ]
        }
        regions = ['mock']

        m.add_service('HelloWorld', 'v1', service_data, regions)
        self.assertIn('HelloWorld', m._active_services)
        self.assertIn('v1', m._active_services['HelloWorld'])
        self.assertIn('instance', m._active_services['HelloWorld']['v1'])
        self.assertIsInstance(
            m._active_services['HelloWorld']['v1']['instance'],
            ExampleService
        )
        if has_service:
            self.assertEqual(
                id(active_services['HelloWorld']['v1']['instance']),
                id(m._active_services['HelloWorld']['v1']['instance'])
            )

        self.assertEqual(
            m._active_services['HelloWorld']['v1']['instance'].args,
            service_args
        )
        self.assertEqual(
            m._active_services['HelloWorld']['v1']['instance'].kwargs,
            service_kwargs
        )
        self.assertEqual(
            len(m._active_services['HelloWorld']['v1']['registrations']),
            0
        )

        service_data['access']['in_service_catalog'] = True
        more_regions = ['flock']
        m.add_service('HelloWorld', 'v1', service_data, more_regions)
        self.assertEqual(
            len(m._active_services['HelloWorld']['v1']['registrations']),
            1
        )
        self.assertEqual(
            len(
                m._active_services[
                    'HelloWorld']['v1']['registrations'][0]['regions']
            ),
            1
        )

    def test_add_requires_keystone_needs_keystone_activate(self):
        m = manager.OpenStackServicesManager()

        service_data = {
            'service': ExampleService,
            'access': {
                'in_service_catalog': True,
                'keystone_service': 'v2',
            },
            'entries': [
                {
                    'version': 1,
                    'type': 'example',
                    'name': 'my example service',
                    'urls': {
                        'public': 'https://{0}/example/v1/'
                    }
                }
            ]
        }
        regions = ['mock']

        with self.assertRaises(manager.ServiceNotAvailable):
            m.add_service('HelloWorld', 'v1', service_data, regions)

    def test_add_requires_keystone_with_keystone_activated(self):
        m = manager.OpenStackServicesManager()

        service_data = {
            'service': ExampleService,
            'access': {
                'in_service_catalog': True,
                'keystone_service': 'v2',
            },
            'entries': [
                {
                    'version': 1,
                    'type': 'example',
                    'name': 'my example service',
                    'urls': {
                        'public': 'https://{0}/example/v1/'
                    }
                }
            ]
        }
        regions = ['mock']

        m.activate_service('Keystone', 'v2', regions)
        m.add_service('HelloWorld', 'v1', service_data, regions)

        self.assertIn('HelloWorld', m._active_services)
        self.assertIn('v1', m._active_services['HelloWorld'])
        self.assertIn('instance', m._active_services['HelloWorld']['v1'])
        self.assertIsInstance(
            m._active_services['HelloWorld']['v1']['instance'],
            ExampleService
        )
        self.assertEqual(
            len(m._active_services['HelloWorld']['v1']['instance'].args),
            1
        )
        self.assertIsInstance(
            m._active_services['HelloWorld']['v1']['instance'].args[0],
            keystone.KeystoneV2Service
        )

    def test_add_and_get(self):
        m = manager.OpenStackServicesManager()

        service_data = {
            'service': ExampleService,
            'access': {
                'in_service_catalog': False,
                'keystone_service': None,
            },
            'entries': [
                {
                    'version': 1,
                    'type': 'example',
                    'name': 'my example service',
                    'urls': {
                        'public': 'https://{0}/example/v1/'
                    }
                }
            ]
        }
        regions = ['mock']

        m.add_service('HelloWorld', 'v1', service_data, regions)

        returned_service = m.get_service('HelloWorld', 'v1')
        self.assertIsInstance(
            returned_service,
            service_data['service']
        )

    @ddt.data(
        ({}, False),
        ({'HelloWorld': {}}, False),
        ({'HelloWorld': {'v1': {}}}, False),
        ({'HelloWorld': {'v1': {'registrations': []}}}, False),
        ({'HelloWorld': {'v1': {'registrations': [{'regions': []}]}}}, False),
        ({'HelloWorld': {'v1': {'registrations': [{'regions': ['mock']}]}}},
            False),
        ({'HelloWorld': {'v1': {'registrations': [{'regions': ['mock']}, {
            'regions': ['albatross']}]}}}, True)
    )
    @ddt.unpack
    def test_del_service(self, active_services, expected_result):
        m = manager.OpenStackServicesManager()
        m._active_services = active_services

        m.del_service('HelloWorld', 'v1', ['mock'])
        self.assertEqual(
            'HelloWorld' in m._active_services,
            expected_result
        )

    @ddt.data(
        {},
        {'HelloWorld': {}},
        {'HelloWorld': {'v1': {}}},
        {'HelloWorld': {'v1': {'registrations': []}}},
        {'HelloWorld': {'v1': {'registrations': [{'regions': []}]}}},
        {'HelloWorld': {'v1': {'registrations': [{'regions': ['mock']}]}}},
        {'HelloWorld': {'v1': {'registrations': [{'regions': ['mock']}, {
            'regions': ['albatross']}]}}},
    )
    def test_reset_all_services(self, active_services):
        m = manager.OpenStackServicesManager()
        m._active_services = active_services
        m.reset_all_services()
        self.assertEqual(len(m._active_services), 0)

    def test_activate_service_not_available(self):
        m = manager.OpenStackServicesManager()
        with self.assertRaises(manager.ServiceNotAvailable):
            m.activate_service('HelloWorld', 'v1', 'mock')

    def test_activate_service_version_not_available(self):
        m = manager.OpenStackServicesManager()
        with self.assertRaises(manager.ServiceVersionNotAvailable):
            m.activate_service('Keystone', 'v1', 'mock')

    def test_activate_service(self):
        m = manager.OpenStackServicesManager()
        m.activate_service('Keystone', 'v2', 'mock')

    @ddt.data(
        ({}, manager.ServiceNotAvailable),
        ({'HelloWorld': {}},
         manager.ServiceVersionNotAvailable),
        ({'HelloWorld': {'v1': {}}},
         None)
    )
    @ddt.unpack
    def test_deactivate_service(self, available_services, exception_raised):
        m = manager.OpenStackServicesManager()
        m._available_services = available_services

        service_name = 'HelloWorld'
        service_version = 'v1'
        regions = ['mock']

        with mock.patch(
            'openstackinabox.manager.OpenStackServicesManager.del_service'
        ) as mock_del_service:
            if exception_raised is not None:
                with self.assertRaises(exception_raised):
                    m.deactivate_service(
                        service_name,
                        service_version,
                        regions
                    )
            else:
                m.deactivate_service(service_name, service_version, regions)

                mock_del_service.assert_called_with(
                    service_name,
                    service_version,
                    available_services[service_name][service_version],
                    regions
                )

    @ddt.data(
        {},
        {'HelloWorld': {}},
        {'HelloWorld': {},
         'WorldHello': {}},
        {'HelloWorld': {'v1': {}},
         'WorldHello': {'v1': {}}},
        {'HelloWorld': {'v1': {}}},
        {'HelloWorld': {'v1': {'registrations': []}}},
        {'HelloWorld': {'v1': {'registrations': []}},
         'WorldHello': {'v1': {'registrations': []}}},
        {'HelloWorld': {'v1': {'instance': ExampleService,
                               'registrations': [{'name': 'Hello',
                                                  'type': 'world',
                                                  'version': 1,
                                                  'regions': [],
                                                  'urls': {}}]}}},
        {
            'HelloWorld': {
                'v1': {
                    'instance': ExampleService,
                    'registrations': [
                        {
                            'name': 'Hello',
                            'type': 'world',
                            'version': 1,
                            'regions': [],
                            'urls': {}
                        }
                    ]
                }
            },
            'WorldHello': {
                'v1': {
                    'instance': ExampleService,
                    'registrations': [
                        {
                            'name': 'Hello',
                            'type': 'world',
                            'version': 1,
                            'regions': [],
                            'urls': {}
                        }
                    ]
                }
            }
        },
        {'HelloWorld': {'v1': {
            'instance': ExampleService,
            'registrations': [{'name': 'Hello',
                               'type': 'world',
                               'version': 1,
                               'regions': ['mock'],
                               'urls': {
                                   'public': 'https://{0}/example/v1/'
                               }}]}}},
        {'HelloWorld': {'v1': {
            'instance': ExampleService,
            'registrations': [{'name': 'Hello',
                               'type': 'world',
                               'version': 1,
                               'regions': ['mock'],
                               'urls': {
                                   'public': 'https://{0}/example/v1/',
                                   'private': 'https://{0}/example/v1/'
                               }}]}}},
        {'HelloWorld': {'v1': {
            'instance': ExampleService,
            'registrations': [{'name': 'Hello',
                               'type': 'world',
                               'version': 1,
                               'regions': ['mock'],
                               'urls': {
                                   'public': 'https://{0}/example/v1/'
                               }}]}},
         'WorldHello': {'v1': {
            'instance': ExampleService,
            'registrations': [{'name': 'Hello',
                               'type': 'world',
                               'version': 1,
                               'regions': ['mock'],
                               'urls': {
                                   'public': 'https://{0}/example/v1/'
                               }}]}}},
        {'HelloWorld': {'v1': {
            'instance': ExampleService,
            'registrations': [{'name': 'Hello',
                               'type': 'world',
                               'version': 1,
                               'regions': ['mock'],
                               'urls': {
                                   'public': 'https://{0}/example/v1/',
                                   'private': 'https://{0}/example/v1/'
                               }}]}},
         'WorldHello': {'v1': {
            'instance': ExampleService,
            'registrations': [{'name': 'Hello',
                               'type': 'world',
                               'version': 1,
                               'regions': ['mock'],
                               'urls': {
                                   'public': 'https://{0}/example/v1/',
                                   'private': 'https://{0}/example/v1/'
                               }}]}}},
    )
    def test_create_service_catalog(self, active_services):
        m = manager.OpenStackServicesManager()
        regions = ['mock']

        m.activate_service('Keystone', 'v2', regions)
        m.keystone_service

        m._active_services = active_services
        m.create_service_catalog()

    @ddt.data(
        {},
        {'HelloWorld': {'v1': {'instance': ExampleService()}}},
    )
    def test_register_services(self, active_services):
        m = manager.OpenStackServicesManager()
        m._active_services = active_services

        m.register_services()
