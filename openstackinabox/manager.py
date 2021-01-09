"""
OpenStackInABox Service Manager
"""
from stackinabox.stack import StackInABox
import six

from openstackinabox.services import (
    cinder,
    keystone
)


class OpenStackServiceManagerException(Exception):
    pass


class ServiceNotAvailable(OpenStackServiceManagerException):
    pass


class ServiceVersionNotAvailable(OpenStackServiceManagerException):
    pass


class KeystoneUrlNotSet(OpenStackServiceManagerException):
    pass


class OpenStackServicesManager(object):
    """
    Service Manager

    Provides the ability to decide what services are instantiated for a test
    and which of those are in the service catalog.

    :ivar dict _available_services: listing of the services available for
        instantiation. The primary key to the dict is the service name (e.g
        Keystone); the secondary is the version.
    :ivar dict _active_services: listing of the services that will be activated
        when the the manager is told to register the services. The primary key
        to the dict is the service name (e.g Keystone); the secondary is
        the version.

    For `_available_services` the basic structure of the dictionary is as
    follows:

    {
        '<name>': {
            '<version>': {
                'service': <python class to instantiate>,
                'access': {
                    'in_service_catalog': <bool>,
                    'keystone_service': None|Keystone's Version String
                },
                'entries': [
                    {
                        'version': version #, (required)
                        'type': <service catalog service type>,
                        'name': <service catalog service name>,
                        'urls': {
                            <url name>: <url format>
                        }
                    }
                ]
            }
        }
    }

    For `_active_services` the basic structure of the dictionary is as
    follows:

    {
        '<name>': {
            '<version>': {
                'instance': <python class instance>,
                'registrations': [
                    {
                        'name': <service catalog name>,
                        'type': <service catalog type>,
                        'regions': [
                            'list',
                            'of',
                            'deployed',
                            'regions'
                        ],
                        'urls': {
                            <url name>: <url format>
                        }
                    }
                ]
            }
        }
    }

    .. note:: Services that need access to Keystone should specify the
        `keystone_service` parameter which will then cause the Keystone
        service instance of the specified version to be passed into it
        via the __init__ parameters.

    .. note:: If the service is not going to be in the Service Catalog
        provided by Keystone, then the `entries` can be simplified just
        to the `version` portion; the type, name, and urls portions can
        be ignored and do not even need to be specified.
    """

    SERVICE_CLASS = 'service'
    SERVICE_INSTANCE = 'instance'
    SERVICE_REGISTRATIONS = 'registrations'
    SERVICE_ACCESS = 'access'
    SERVICE_IN_CATALOG = 'in_service_catalog'
    SERVICE_NEED_KEYSTONE = 'keystone_service'
    SERVICE_ENTRIES = 'entries'
    SERVICE_ENTRIES_VERSION = 'version'
    SERVICE_ENTRIES_TYPE = 'type'
    SERVICE_ENTRIES_NAME = 'name'
    SERVICE_ENTRIES_URLS = 'urls'
    SERVICE_ENTRIES_REGIONS = 'regions'

    def __init__(self):
        self._keystone_service = None
        self._identity_url_template = "https://{0}/keystone/v2.0/"
        self._identity_url = None
        self._base_url = 'localhost'
        self._available_regions = [
            'mock'
        ]
        self._available_services = {
            'Keystone': {
                'v2': {
                    self.SERVICE_CLASS: keystone.KeystoneV2Service,
                    self.SERVICE_ACCESS: {
                        self.SERVICE_IN_CATALOG: False,
                        self.SERVICE_NEED_KEYSTONE: None,
                    },
                    self.SERVICE_ENTRIES: [
                        {
                            self.SERVICE_ENTRIES_VERSION: 2,
                        }
                    ]
                }
            },
            'Cinder': {
                'v1': {
                    self.SERVICE_CLASS: cinder.CinderV1Service,
                    self.SERVICE_ACCESS: {
                        self.SERVICE_IN_CATALOG: True,
                        self.SERVICE_NEED_KEYSTONE: 'v2',
                    },
                    self.SERVICE_ENTRIES: [
                        {
                            self.SERVICE_ENTRIES_VERSION: 1,
                            self.SERVICE_ENTRIES_TYPE: 'volume',
                            self.SERVICE_ENTRIES_NAME: 'cloudBlockStorage',
                            self.SERVICE_ENTRIES_URLS: {
                                'publicURL': 'https://{0}/cinder/v1/'
                            }
                        }
                    ]
                }
            }
        }
        # _active_services should look like _available_services
        self._active_services = {
        }

    @property
    def keystone_service(self):
        """
        Access the Keystone Service (Keystone v2)

        :retval: KeystoneV2Service instance
        """
        if self._keystone_service is None:
            self._keystone_service = self.get_service('Keystone', 'v2')

        return self._keystone_service

    @property
    def identity_url(self):
        """
        Retrieve the Identity URL

        :raises: KeystoneUrlNotSet if URL has not yet been set. Create the
            service catalog entries to configure the Identity URL.
        """
        if self._identity_url is None:
            raise KeystoneUrlNotSet("Keystone URL not yet set")

        return self._identity_url

    @property
    def base_url(self):
        """
        Access the Base URL used by StackInABox
        """
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        """
        Set the Base URL used with StackInABox
        """
        self._base_url = value

    def get_service(self, service_name, service_version):
        """
        Active a specific service and version in a given set of regions

        .. note:: The service must be in the built-in known services.

        :param unicode service_name: name of the service
        :param unicode service_version: version of the service

        :raises: ServiceNotAvailable if the service or service version is not
            supported

        :retval: dict containign the service data
        """
        try:
            return (
                self._active_services[service_name][service_version][
                    self.SERVICE_INSTANCE]
            )

        except KeyError:
            raise ServiceNotAvailable(
                'Service {0} with version {1} has not been '
                'activated yet'.format(
                    service_name,
                    service_version
                )
            )

    def reset_all_services(self):
        removal_set = []
        for service_name, service_version in six.iteritems(
            self._active_services
        ):
            for version, info in six.iteritems(service_version):
                regions = []
                if self.SERVICE_REGISTRATIONS in info:
                    for r in info[self.SERVICE_REGISTRATIONS]:
                        regions.extend(r[self.SERVICE_ENTRIES_REGIONS])
                removal_set.append(
                    (service_name, version, regions)
                )
        for entry in removal_set:
            self.del_service(*entry)
        self._active_services = {}

    def add_service(
        self, service_name, service_version, service_data, regions
    ):
        """
        Add a specific service and version in a given set of regions

        .. note:: This is independent of the internally known built-in
            services, and can be used to add random services into the system.

        The service_data dict has the following format:

            {
                'service': <Uninstantiated StackInABox Service Class>,
                'access': {
                    'in_service_catalog': bool,
                    'keystone_service': None
                }
                'entries: [
                    {
                        'version': <service version>,
                        'type': <service catalog service type>,
                        'name': <service catalog service name>,
                        'urls': {
                            <url name>: <url format>
                        }
                    }
                ]
            }

        If the service_data['access']['in_service_catalog'] is True then the
        entry will be included in the service catalog. Each dict the
        service_data['entries'] is converted into a Service Catalog
        registration, at which point the URLs formatted with the Base URL.

        .. note:: All regions instantiated will point to the same StackInABox
            Service instance. To get true multi-region support, simply set the
            Base URL to a region specific value (e.g localhost.region1), and
            then add the services for that region.

        :param unicode service_name: name of the service
        :param unicode service_version: version of the service
        :param dict service_data: A dict containg the information about the
            service to be added.
        :param list regions: list of regions the service is to be available in

        :raises: ServiceNotAvailable if the service is not supported
        :raises: ServiceVersionNotAvailable if the service version is not
            supported
        """
        if service_name not in self._active_services:
            self._active_services[service_name] = {}

        if service_version not in self._active_services[service_name]:
            self._active_services[service_name][service_version] = {}

        registrations = []
        if service_data[self.SERVICE_ACCESS][self.SERVICE_IN_CATALOG]:
            registrations.extend(
                [
                    {
                        self.SERVICE_ENTRIES_NAME: entry[
                            self.SERVICE_ENTRIES_NAME],
                        self.SERVICE_ENTRIES_TYPE: entry[
                            self.SERVICE_ENTRIES_TYPE],
                        self.SERVICE_ENTRIES_VERSION: entry[
                            self.SERVICE_ENTRIES_VERSION],
                        self.SERVICE_ENTRIES_REGIONS: regions,
                        self.SERVICE_ENTRIES_URLS: entry[
                            self.SERVICE_ENTRIES_URLS]
                    }
                    for entry in service_data[self.SERVICE_ENTRIES]
                ]
            )

        if (
            self.SERVICE_INSTANCE not in
            self._active_services[service_name][service_version]
        ):
            args = []
            if (
                service_data[self.SERVICE_ACCESS][
                    self.SERVICE_NEED_KEYSTONE] is not None
            ):
                args.append(
                    self.get_service(
                        'Keystone',
                        service_data[self.SERVICE_ACCESS][
                            self.SERVICE_NEED_KEYSTONE]
                    )
                )

            self._active_services[service_name][service_version] = {
                self.SERVICE_INSTANCE: service_data[self.SERVICE_CLASS](*args),
                self.SERVICE_REGISTRATIONS: registrations
            }
        else:
            self._active_services[service_name][service_version][
                self.SERVICE_REGISTRATIONS].extend(registrations)

    def del_service(self, service_name, service_version, regions):
        """
        Remove a specific service and version in a given set of regions

        .. note:: This is independent of the internally known built-in
            services, and can be used to remove random services from the
            system.

        :param unicode service_name: name of the service
        :param unicode service_version: version of the service
        :param list regions: list of regions to remove the service from
        """
        def remove_region(registration_count):
            for region in regions:
                if (
                    region in self._active_services[service_name][
                        service_version][self.SERVICE_REGISTRATIONS][
                            registration_count][self.SERVICE_ENTRIES_REGIONS]
                ):
                    self._active_services[service_name][service_version][
                        self.SERVICE_REGISTRATIONS][registration_count][
                            self.SERVICE_ENTRIES_REGIONS].remove(
                        region
                    )

        def remove_registrations():
            total_registrations = len(
                self._active_services[
                    service_name][service_version][
                        self.SERVICE_REGISTRATIONS]
            )

            registrations_to_remove = []
            for registration_count in range(total_registrations):
                remove_region(registration_count)
                if not len(self._active_services[
                    service_name][service_version][
                        self.SERVICE_REGISTRATIONS][registration_count][
                            self.SERVICE_ENTRIES_REGIONS]
                ):
                    registrations_to_remove.append(registration_count)

            registrations_to_remove.reverse()

            for count in registrations_to_remove:
                del self._active_services[
                    service_name][service_version][
                        self.SERVICE_REGISTRATIONS][count]

        def remove_version():
            if service_version in self._active_services[service_name]:
                if (
                    self.SERVICE_REGISTRATIONS in self._active_services[
                        service_name][service_version]
                ):
                    remove_registrations()
                    if not len(
                        self._active_services[service_name][service_version][
                            self.SERVICE_REGISTRATIONS]
                    ):
                        del self._active_services[service_name][
                            service_version]
                else:
                    del self._active_services[service_name][service_version]

        if service_name in self._active_services:
            remove_version()
            if not len(self._active_services[service_name]):
                del self._active_services[service_name]

    def activate_service(self, service_name, service_version, regions):
        """
        Active a specific service and version in a given set of regions

        .. note:: The service must be in the built-in known services.

        :param unicode service_name: name of the service
        :param unicode service_version: version of the service
        :param list regions: list of regions the service is to be available in

        :raises: ServiceNotAvailable if the service is not supported
        :raises: ServiceVersionNotAvailable if the service version is not
            supported
        """
        if service_name in self._available_services:
            if service_version in self._available_services[service_name]:
                self.add_service(
                    service_name,
                    service_version,
                    self._available_services[service_name][service_version],
                    regions
                )
            else:
                raise ServiceVersionNotAvailable(
                    "Service {0} does not have a version {1}".format(
                        service_name,
                        service_version
                    )
                )
        else:
            raise ServiceNotAvailable(
                "Service {0} is not in the available services".format(
                    service_name
                )
            )

    def deactivate_service(self, service_name, service_version, regions):
        """
        Deactivate a specific service and version in a given set of regions

        .. note:: The service must be in the built-in known services.

        :param unicode service_name: name of the service
        :param unicode service_version: version of the service
        :param list regions: list of regions the service is to be available in

        :raises: ServiceNotAvailable if the service is not supported
        :raises: ServiceVersionNotAvailable if the service version is not
            supported
        """
        if service_name in self._available_services:
            if service_version in self._available_services[service_name]:
                self.del_service(
                    service_name,
                    service_version,
                    self._available_services[service_name][service_version],
                    regions
                )
            else:
                raise ServiceVersionNotAvailable(
                    "Service {0} does not have a version {1}".format(
                        service_name,
                        service_version
                    )
                )
        else:
            raise ServiceNotAvailable(
                "Service {0} is not in the available services".format(
                    service_name
                )
            )

    def create_service_catalog(self):
        """
        Register all the active OpenStack Services with Keystone so they
        show up in the service catalog.
        """
        self._identity_url = self._identity_url_template.format(
            self.base_url
        )
        for service_name, service in six.iteritems(self._active_services):
            for service_version, service_data in six.iteritems(service):
                if self.SERVICE_REGISTRATIONS in service_data:
                    for registration in service_data[
                        self.SERVICE_REGISTRATIONS
                    ]:
                        service_id = self.keystone_service.model.services.add(
                            registration[self.SERVICE_ENTRIES_NAME],
                            registration[self.SERVICE_ENTRIES_TYPE]
                        )
                        for region in registration[
                            self.SERVICE_ENTRIES_REGIONS
                        ]:
                            endpoint_id = self.keystone_service.model.\
                                endpoints.add(
                                    service_id,
                                    region,
                                    '',  # no version info
                                    '',  # no version list
                                    registration[self.SERVICE_ENTRIES_VERSION]
                                )
                            for url_name, url in six.iteritems(
                                registration[self.SERVICE_ENTRIES_URLS]
                            ):
                                self.keystone_service.model.endpoints.add_url(
                                    endpoint_id,
                                    url_name,
                                    url.format(self.base_url)
                                )

    def register_services(self):
        """
        Register the Active OpenStack services with StackInABox
        """
        for service_name, service in six.iteritems(self._active_services):
            for service_version, service_data in six.iteritems(service):
                StackInABox.register_service(
                    service_data[self.SERVICE_INSTANCE]
                )
