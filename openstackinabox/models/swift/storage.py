"""
"""
import hashlib
import io
import logging
import os
import os.path

import six
from stackinabox.util.tools import CaseInsensitiveDict

from openstackinabox.utils.directory import TemporaryDirectory

from openstackinabox.models.swift import exceptions


LOG = logging.getLogger(__name__)


class SwiftStorage(object):

    @staticmethod
    def get_etag(data):
        etag_generator = hashlib.md5()
        etag_generator.update(data)

        return etag_generator.hexdigest()

    @staticmethod
    def get_file_etag(file_name):
        etag_generator = hashlib.md5()
        with open(file_name, 'rb') as input_data:
            for chunk in input_data:
                etag_generator.update(chunk)

        return etag_generator.hexdigest()

    def __init__(self, service_id, model):
        self.__id = service_id
        self.__model = model
        self.__storage = TemporaryDirectory()
        self.__metadata_information = {}
        self.__custom_metadata = {}

    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, value):
        self.__model = value

    @property
    def storage(self):
        return self.__storage

    @property
    def location(self):
        return self.storage.name

    @property
    def metadata(self):
        return self.__metadata_information

    @property
    def custom_metadata(self):
        return self.__custom_metadata

    def get_tenant_path(self, tenantid):
        return '{0}/{1}'.format(self.location, tenantid)

    def get_container_path(self, tenantid, container_name):
        return '{0}/{1}'.format(
            self.get_tenant_path(tenantid),
            container_name
        )

    def get_object_path(self, tenantid, container_name, object_name):
        try:
            intTenantId = self.model.has_tenant(tenantid)
            intContainerId = self.model.has_container(
                intTenantId,
                container_name
            )

            intObjectId = self.model.has_object(
                intTenantId,
                intContainerId,
                object_name
            )

            object_info = self.model.get_object(
                intTenantId,
                intContainerId,
                intObjectId
            )

            return object_info['path']

        except (
            exceptions.SwiftUnknownTenantError,
            exceptions.SwiftUnknownContainerError,
            exceptions.SwiftUnknownObjectError
        ):
            LOG.exception(
                'Swift Service ({0}): Failed to retrieved path for Object '
                '{3} in Container {2} for Tenant {1}'.format(
                    self.__id, tenantid, container_name, object_name
                )
            )
            raise

    def add_tenant(self, tenantid):
        LOG.debug(
            'Swift Service ({0}): Checking if Tenant {1} exists...'.format(
                self.__id, tenantid
            )
        )

        path = None
        try:
            intTenantId = self.model.has_tenant(tenantid)

            tenant_data = self.model.get_tenant(intTenantId)
            path = tenant_data['path']

        except exceptions.SwiftUnknownTenantError:
            path = self.get_tenant_path(tenantid)
            LOG.exception(
                'SwiftService ({0}): Adding Tenant {1} at path {2}'.format(
                    self.__id, tenantid, path
                )
            )
            intTenantId = self.model.add_tenant(tenantid, path)

        if not os.path.exists(path):
            LOG.debug(
                'SwiftService ({0}): Creating path for Tenant {1} at '
                '{2}'.format(
                    self.__id, tenantid, path
                )
            )
            os.mkdir(path)

        return intTenantId

    def has_tenant(self, tenantid):
        try:
            intTenantId = self.model.has_tenant(tenantid)

            tenant_info = self.model.get_tenant(intTenantId)
            return os.path.exists(tenant_info['path'])

        except Exception:
            LOG.exception(
                'SwiftService ({0}): Unknown Tenant {1}'.format(
                    self.__id, tenantid
                )
            )
            return False

    def add_container(self, tenantid, container_name):
        LOG.debug(
            'Swift Service ({0}): Checking for container\'s tenant - '
            '{1}'.format(
                self.__id, tenantid
            )
        )

        intTenantId = None
        try:
            intTenantId = self.model.has_tenant(tenantid)

        except exceptions.SwiftUnknownTenantError:
            LOG.exception(
                'SwiftService ({0}): Adding Unknown Tenant {1}...'.format(
                    self.__id, tenantid
                )
            )
            intTenantId = self.add_tenant(tenantid)

        LOG.debug(
            'Swift Service ({0}): Checking that container {2} exists for '
            'tenant {1}'.format(
                self.__id, tenantid, container_name
            )
        )
        path = self.get_container_path(tenantid, container_name)
        intContainerId = self.model.add_container(
            intTenantId,
            container_name,
            path
        )

        if not os.path.exists(path):
            LOG.debug(
                'SwiftService ({0}): Adding Container {2} for Tenant {1} at '
                'path {3}'.format(
                    self.__id, tenantid, container_name, path
                )
            )
            os.mkdir(path)

        return (intTenantId, intContainerId)

    def has_container(self, tenantid, container_name):
        try:
            intTenantId = self.model.has_tenant(tenantid)
            intContainerId = self.model.has_container(
                intTenantId,
                container_name
            )
            container_info = self.model.get_container(
                intTenantId,
                intContainerId
            )
            path = container_info['path']
            return os.path.exists(path)

        except Exception:
            LOG.exception(
                'SwiftService ({0}): Unknown Container {2} or Tenant '
                '{1}'.format(
                    self.__id, tenantid, container_name
                )
            )
            return False

    def get_container(self, tenantid, container_name):
        try:
            intTenantId = self.model.has_tenant(tenantid)
            intContainerId = self.model.has_container(
                intTenantId,
                container_name
            )
            return (intTenantId, intContainerId)

        except Exception:
            LOG.exception(
                'SwiftService ({0}): Unknown Container {2} or Tenant '
                '{1}'.format(
                    self.__id, tenantid, container_name
                )
            )
            return (None, None)

    def has_object(self, tenantid, container_name, object_name):
        try:
            intTenantId = self.model.has_tenant(tenantid)
            intContainerId = self.model.has_container(
                intTenantId,
                container_name
            )
            intObjectId = self.model.has_object(
                intTenantId,
                intContainerId,
                object_name
            )
            object_info = self.model.get_object(
                intTenantId,
                intContainerId,
                intObjectId
            )

            path = object_info['path']
            return os.path.exists(path)

        except Exception:
            LOG.exception(
                'Swift Service ({0}): Unknown Object {3}, Container {2}, or '
                'Tenant {1}'.format(
                    self.__id, tenantid, container_name, object_name
                )
            )
            return False

    def load_object_from_file(
        self, tenantid, container_name, object_name, file_name, file_size=None,
        allow_file_size_mismatch=False
    ):
        LOG.debug(
            'Swift Service ({0}): Checking that tenant {1} has container '
            '{2}'.format(
                tenantid, container_name, object_name
            )
        )
        if not self.has_container(tenantid, container_name):
            self.add_container(tenantid, container_name)

        LOG.debug(
            'Swift Service ({0}): Loading object {3} from file into container '
            '{2} for tenant {1}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )

        actual_file_size = (
            file_size
            if file_size
            else os.path.getsize(file_name)
        )

        metadata = CaseInsensitiveDict()
        metadata.update(
            {
                'content-length': str(actual_file_size),
                'content-type': 'application/binary',
                'etag': self.get_file_etag(file_name)
            }
        )
        with open(file_name, 'rb') as content:
            self.store_object(
                tenantid, container_name, object_name, content,
                metadata, actual_file_size, allow_file_size_mismatch
            )

    def load_object(
        self, tenantid, container_name, object_name, content, file_size=None,
        allow_file_size_mismatch=False
    ):
        LOG.debug(
            'Swift Service ({0}): Checking that tenant {1} has container '
            '{2}'.format(
                tenantid, container_name, object_name
            )
        )
        if not self.has_container(tenantid, container_name):
            self.add_container(tenantid, container_name)

        LOG.debug(
            'Swift Service ({0}): Loading object {3} from python object into '
            'containter {2} for tenant {1}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )

        actual_file_size = (
            file_size
            if file_size
            else len(content)
        )

        metadata = CaseInsensitiveDict()
        metadata.update({
            'content-length': str(actual_file_size),
            'content-type': 'application/binary',
            'etag': self.get_etag(content)
        })
        self.store_object(
            tenantid, container_name, object_name, content, metadata,
            actual_file_size, allow_file_size_mismatch
        )

    def update_object_etag(
        self, tenantid, container_name, object_name, new_etag
    ):
        path = self.get_object_path(tenantid, container_name, object_name)
        if path in self.metadata:
            self.metadata[path]['etag'] = new_etag

    def store_or_update_custom_metadata(
        self, tenantid, container_name, object_name, metadata
    ):
        LOG.debug(
            'Swift Service ({0}): Storing custom metadata - {1}'.format(
                self.__id, metadata
            )
        )
        path = self.get_object_path(tenantid, container_name, object_name)
        if path in self.custom_metadata:
            LOG.debug(
                'Swift Service ({0}): Updating existing custom metadata {1} '
                'with {2}'.format(
                    self.__id,
                    self.custom_metadata[path],
                    metadata
                )
            )
            self.custom_metadata[path].update(metadata)
            LOG.debug(
                'Swift Service ({0}): updated existing custom metadata '
                '{1}'.format(
                    self.__id, self.custom_metadata[path]
                )
            )
        else:
            LOG.debug('Swift Service ({0}): no existing custom metadata')
            self.custom_metadata[path] = metadata
            LOG.debug(
                'Swift Service ({0}): saved custom metadata {1}'.format(
                    self.__id, self.custom_metadata[path]
                )
            )

    def retrieve_custom_metadata(self, tenantid, container_name, object_name):
        custom_metadata = CaseInsensitiveDict()

        path = self.get_object_path(tenantid, container_name, object_name)
        if path in self.custom_metadata:
            custom_metadata.update(self.custom_metadata[path])

        return custom_metadata

    def remove_custom_metadata(self, tenantid, container_name, object_name):
        path = self.get_object_path(tenantid, container_name, object_name)
        if path in self.custom_metadata:
            del self.custom_metadata[path]

    def store_object(
        self, tenantid, container_name, object_name, content, metadata,
        file_size=None, allow_file_size_mismatch=False
    ):
        path = None
        if self.has_container(tenantid, container_name):
            intTenantId, intContainerId = self.get_container(
                tenantid,
                container_name
            )

        else:
            intTenantId, intContainerId = self.add_container(
                tenantid,
                container_name
            )

        try:
            path = self.get_object_path(tenantid, container_name, object_name)

        except (
            exceptions.SwiftUnknownTenantError,
            exceptions.SwiftUnknownContainerError,
            exceptions.SwiftUnknownObjectError
        ):

            # no way it can already have the object...
            path = '{0}/{1}'.format(
                self.get_container_path(tenantid, container_name),
                object_name
            )

        LOG.debug(
            'Swift Service ({0}): Using path {1} for object '
            '{2}/{3}:{4}'.format(
                self.__id, path, tenantid, container_name, object_name
            )
        )

        self.model.add_object(intTenantId, intContainerId, object_name, path)

        LOG.debug(
            'Swift Service ({0}): Added object {1}/{2}/{3}:{4} to model'
            .format(
                self.__id, path, tenantid, container_name, object_name
            )
        )

        with open(path, 'wb') as object_file:
            if content:
                object_file.write(content)

            object_file.flush()

        LOG.debug('Swift Service ({0}): object data stored'.format(self.__id))

        for k, v in six.iteritems(metadata):
            LOG.debug(
                'Swift Service ({0}): Storing Metadata[{1}] = {2}'.format(
                    self.__id, k, v
                )
            )

        if file_size is None:
            file_size = os.path.getsize(path)

        LOG.debug(
            'Swift Service ({0}): object has disk size of {1} bytes'.format(
                self.__id, file_size
            )
        )

        if int(metadata['content-length']) != file_size:
            LOG.debug(
                'Swift Service ({0}): {1} != {2}. Object not stored on disk '
                'properly'.format(
                    self.__id, metadata['content-length'], file_size
                )
            )
            if not allow_file_size_mismatch:
                LOG.debug(
                    'Swift Service ({0}): File on disk must match specified '
                    'file size. ERROR!!!'.format(
                        self.__id
                    )
                )
                raise RuntimeError(
                    'Swift Service ({0}): Failed to store all bytes for the '
                    'object'.format(
                        self.__id
                    )
                )

            else:
                LOG.debug(
                    'Swift Service ({0}): File on disk may differ specified '
                    'file size.'.format(
                        self.__id
                    )
                )

        metadata['x-y-object-disk-path'] = path

        for k, v in six.iteritems(metadata):
            LOG.debug(
                'Swift Service ({0}): Storing Metadata - {1} = {2}'.format(
                    self.__id, k, v
                )
            )
        self.metadata[path] = metadata
        LOG.debug('Swift Service ({0}): Metadata stored'.format(self.__id))

    def retrieve_object(self, tenantid, container_name, object_name):
        if self.has_object(tenantid, container_name, object_name):
            metadata = CaseInsensitiveDict()
            path = self.get_object_path(
                tenantid,
                container_name,
                object_name
            )
            if path in self.metadata:
                metadata.update(self.metadata[path])

            custom_metadata = self.retrieve_custom_metadata(
                tenantid, container_name, object_name
            )
            for k, v in six.iteritems(custom_metadata):
                LOG.debug(
                    'Swift Service ({0}): Custom Metadata[{1}] = {2} with '
                    'type {3}'.format(
                        self.__id, k, v, type(v)
                    )
                )
            metadata.update(custom_metadata)

            LOG.debug(
                'Swift Service ({0}): Returning metadata - {1}'.format(
                    self.__id, metadata
                )
            )

            if 'content-length' in metadata:
                LOG.debug(
                    'Swift Service ({0}): Metadata data length - {1}'.format(
                        self.__id, metadata['content-length']
                    )
                )

            data = None
            try:
                with open(path, 'rb') as data_input:
                    data = io.BytesIO(data_input.read())

                data.seek(0, os.SEEK_END)
                LOG.debug(
                    'Swift Service ({0}): Returning length - {1}'.format(
                        self.__id, data.tell()
                    )
                )
                data.seek(0, os.SEEK_SET)

            except Exception:
                LOG.exception('Failed to read object from disk')
                data = None

            return (data,
                    metadata)

        else:
            LOG.debug('Swift Service ({0}): No object.'.format(self.__id))
            return (None, None)

    def remove_object(self, tenantid, container_name, object_name):
        if self.has_object(tenantid, container_name, object_name):
            intTenantId, intContainerId = self.get_container(
                tenantid, container_name
            )

            path = self.get_object_path(tenantid, container_name, object_name)
            LOG.debug(
                'Swift Service ({0}): Using path {1} for object '
                '{2}/{3}:{4}'.format(
                    self.__id, path, tenantid, container_name, object_name
                )
            )

            intTenantId = self.model.has_tenant(tenantid)
            intContainerId = self.model.has_container(
                intTenantId, container_name
            )
            intObjectId = self.model.has_object(
                intTenantId, intContainerId, object_name
            )
            LOG.debug(
                'Swift Service ({0}): T: {1}, C: {2}, O: {3}'.format(
                    self.__id, intTenantId, intContainerId, intObjectId
                )
            )

            self.model.remove_object(
                intTenantId, intContainerId, intObjectId
            )

            LOG.debug(
                'Swift Service ({0}): removed object from model'.format(
                    self.__id
                )
            )

            os.remove(path)
            LOG.debug(
                'Swift Service ({0}): removed object from disk'.format(
                    self.__id
                )
            )

        else:
            LOG.debug(
                'Swift Service ({0}): No object to remove'.format(self.__id)
            )
