"""
OpenStack Swift Services
"""

"""
StackInABox - Swift Service Mock
"""
import datetime
import hashlib
import io
import logging
import os
import os.path
import re
import sqlite3
import uuid

import six
from stackinabox.services.service import StackInABoxService
from stackinabox.util.tools import CaseInsensitiveDict

from openstackinabox.services import base_service
from openstackinabox.utils.directory import TemporaryDirectory


schema = [
    '''
    CREATE TABLE swift_tenants
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenantid TEXT NOT NULL,
        path TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE swift_containers
    (
        tenantid INTEGER NOT NULL REFERENCES swift_tenants(id),
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_name TEXT NOT NULL,
        path TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE swift_objects
    (
        tenantid INTEGER NOT NULL REFERENCES swift_tenants(id),
        containerid INTEGER NOT NULL REFERENCES swift_containers(id),
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_name TEXT NOT NULL,
        path TEXT NOT NULL
    )
    '''
]

SQL_INSERT_TENANT = '''
    INSERT INTO swift_tenants
    (tenantid, path)
    VALUES(:tenantid, :path)
'''
SQL_GET_TENANT = '''
    SELECT id, tenantid, path
    FROM swift_tenants
    WHERE id = :id
'''
SQL_HAS_TENANT = '''
    SELECT id
    FROM swift_tenants
    WHERE tenantid = :tenantid
'''

SQL_INSERT_CONTAINER = '''
    INSERT INTO swift_containers
    (tenantid, container_name, path)
    VALUES (:tenantid, :container_name, :path)
'''
SQL_GET_CONTAINER = '''
    SELECT tenantid, id, container_name, path
    FROM swift_containers
    WHERE tenantid = :tenantid
      AND id = :containerid
'''
SQL_HAS_CONTAINER = '''
    SELECT id
    FROM swift_containers
    WHERE tenantid = :tenantid
      AND container_name = :container_name
'''

SQL_INSERT_OBJECT = '''
    INSERT INTO swift_objects
    (tenantid, containerid, object_name, path)
    VALUES(:tenantid, :containerid, :object_name, :path)
'''
SQL_GET_OBJECT = '''
    SELECT tenantid, containerid, id, object_name, path
    FROM swift_objects
    WHERE tenantid = :tenantid
      AND containerid = :containerid
      AND id = :objectid
'''
SQL_HAS_OBJECT = '''
    SELECT id
    FROM swift_objects
    WHERE tenantid = :tenantid
      AND containerid = :containerid
      AND object_name = :object_name
'''
SQL_REMOVE_DELETE = '''
    DELETE
    FROM swift_objects
    WHERE tenantid = :tenantid
      AND containerid = :containerid
      AND id = :objectid
'''


class SwiftExceptions(Exception):
    pass


class SwiftUnknownTenantError(SwiftExceptions):
    pass


class SwiftUnknownContainerError(SwiftExceptions):
    pass


class SwiftUnknownObjectError(SwiftExceptions):
    pass


class SwiftServiceModel(object):

    def __init__(self):
        self.__db = sqlite3.connect(':memory:')
        self.__init_database()

    def __init_database(self):
        cursor = self.__db.cursor()
        for table_sql in schema:
            cursor.execute(table_sql)
        self.__db.commit()

    def has_tenant(self, tenantid):
        cursor = self.__db.cursor()
        args = {
            'tenantid': tenantid
        }
        cursor.execute(SQL_HAS_TENANT, args)
        result = cursor.fetchone()
        if result is None:
            raise SwiftUnknownTenantError(
                'Unknown tenant {0}'.format(tenantid))

        return result[0]

    def add_tenant(self, tenantid, path):
        cursor = self.__db.cursor()
        args = {
            'tenantid': tenantid,
            'path': path
        }
        cursor.execute(SQL_INSERT_TENANT, args)
        self.__db.commit()

        return self.has_tenant(tenantid)

    def get_tenant(self, internal_tenant_id):
        cursor = self.__db.cursor()
        args = {
            'id': internal_tenant_id
        }
        cursor.execute(SQL_GET_TENANT)
        result = cursor.fetchone()
        if result is None:
            raise SwiftUnknownTenantError(
                'Unknown tenant with internal id {0}'.format(tenantid))

        return {
            'id': result[0],
            'tenantid': result[1],
            'path': result[2]
        }

    def has_container(self, internal_tenant_id, container_name):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'container_name': container_name
        }
        cursor.execute(SQL_HAS_CONTAINER, args)
        result = cursor.fetchone()
        if result is None:
            raise SwiftUnknownContainerError(
                'Unknown container {1} under internal tenant id {0}'
                .format(internal_tenant_id, container_name))

        return result[0]

    def add_container(self, internal_tenant_id, container_name, path):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'container_name': container_name,
            'path': path
        }
        cursor.execute(SQL_INSERT_CONTAINER, args)
        self.__db.commit()

        return self.has_container(internal_tenant_id, container_name)

    def get_container(self, internal_tenant_id, internal_container_id):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id
        }
        cursor.execute(SQL_GET_CONTAINER, args)
        result = cursor.fetchone()
        if result is None:
            raise SwiftUnknownContainerError(
                'Unknown container {1} under internal tenant id {0}'
                .format(internal_tenant_id, container_name))

        return {
            'tenantid': result[0],
            'containerid': result[1],
            'container_name': result[2],
            'path': result[3]
        }

    def has_object(self, internal_tenant_id, internal_container_id,
                   object_name):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'object_name': object_name
        }
        cursor.execute(SQL_HAS_OBJECT, args)
        result = cursor.fetchone()
        if result is None:
            raise SwiftUnknownObjectError(
                'Unknown object {2} with internal container id {1} '
                'under internal tenant id {0}'
                .format(internal_tenant_id,
                        internal_container_id,
                        object_name))

        return result[0]

    def add_object(self, internal_tenant_id, internal_container_id,
                   object_name, path):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'object_name': object_name,
            'path': path
        }
        cursor.execute(SQL_INSERT_OBJECT, args)
        self.__db.commit()

        return self.has_object(internal_tenant_id,
                               internal_container_id,
                               object_name)

    def get_object(self, internal_tenant_id, internal_container_id,
                   internal_object_id):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'objectid': internal_object_id,
        }
        cursor.execute(SQL_GET_OBJECT, args)
        result = cursor.fetchone()
        if result is None:
            raise SwiftUnknownObjectError(
                'Unknown object {2} with internal container id {1} '
                'under internal tenant id {0}'
                .format(internal_tenant_id,
                        internal_container_id,
                        object_name))

        return {
            'tenantid': result[0],
            'containerid': result[1],
            'objectid': result[2],
            'object_name': result[3],
            'path': result[4]
        }

    def remove_object(self, internal_tenant_id, internal_container_id,
                      internal_object_id):
        cursor = self.__db.cursor()
        args = {
            'tenantid': internal_tenant_id,
            'containerid': internal_container_id,
            'objectid': internal_object_id,
        }
        cursor.execute(SQL_REMOVE_DELETE, args)
        self.__db.commit()


class SwiftService(base_service.BaseService):

    # URL_REGEX = re.compile('\A\/(.+)\/(.+)\/(.+)\Z')
    word_match = '([\.%~#@!&\^\*\(\)\+=\`\'":;><?\w-]+)'
    URL_REGEX = re.compile('\A\/{0}\/{0}\/(.+\Z)'
                           .format(word_match))

    @staticmethod
    def split_uri(uri):
        self.log_debug('SwiftService: Attempting to split URL: {0} using regex '
                     '{1}'
                     .format(uri, SwiftService.URL_REGEX.pattern))
        data = SwiftService.URL_REGEX.match(uri)
        if data:
            data_groups = data.groups()
            self.log_debug('SwiftService: Split URL into {0} groups'
                         .format(len(data_groups)))

            for dg in data_groups:
                self.log_debug('SwiftService: Split URL - group: {0}'
                             .format(dg))

            return (data_groups[0], data_groups[1], data_groups[2])

        self.log_debug('Swift Service: Failed to split url')
        return (None, None, None)

    @staticmethod
    def sanitize_name(name):
        if '\\' in name:
            self.log_debug('Swift Service: Updating object name to replace '
                         '"\" with " "')
            name = name.replace('\\', ' ')

        if '/' in name:
            self.log_debug('Swift Service: Updating object name to replace '
                         '"/" with " "')
            name = name.replace('/', ' ')

        return name

    def __init__(self):
        super(SwiftService, self).__init__('swift/v1.0')
        self.__model = SwiftServiceModel()
        self.__id = uuid.uuid4()
        self.__storage = TemporaryDirectory()
        self.__storage_location = self.__storage.name
        self.__metadata_information = {}
        self.__custom_metadata = {}
        self.fail_auth = False
        self.fail_error_code = None

    def do_register_object(self, tenantid, container_name, object_name):
        uri = '/{0}/{1}/{2}'.format(tenantid,
                                   container_name,
                                   object_name)
        self.log_debug(
            'SwiftService ({0}): Registering Object Service for '
            'T/C:O - {1}/{2}: {3}'
            .format(self.__id, tenantid, container_name, object_name))
        self.register(StackInABoxService.GET,
                      uri,
                      SwiftService.get_object_handler)
        self.register(StackInABoxService.PUT,
                      uri,
                      SwiftService.put_object_handler)
        self.register(StackInABoxService.POST,
                      uri,
                      SwiftService.put_object_handler)
        self.register(StackInABoxService.HEAD,
                      uri,
                      SwiftService.head_object_handler)
        self.register(StackInABoxService.DELETE,
                      uri,
                      SwiftService.delete_object_handler)

    def __get_tenant_path(self, tenantid):
        return '{0}/{1}'.format(self.__storage_location,
                                tenantid)

    def __get_container_path(self, tenantid, container_name):
        return '{0}/{1}'.format(self.__get_tenant_path(tenantid),
                                container_name)

    def __get_object_path(self, tenantid, container_name, object_name):
        if self.has_object(tenantid, container_name, object_name):
            try:
                intTenantId = self.__model.has_tenant(tenantid)
                intContainerId = self.__model.has_container(intTenantId,
                                                            container_name)
                intObjectId = self.__model.has_object(intTenantId,
                                                      intContainerId,
                                                      object_name)
                object_info = self.__model.get_object(intTenantId,
                                                      intContainerId,
                                                      intObjectId)

                return object_info['path']

            except Exception:
                self.log_exception(
                    'Swift Service ({0}): Failed to retrieved path for Object '
                    '{3} in Container {2} for Tenant {1}'
                    .format(self.__id, tenantid, container_name, object_name))

        else:
            return '{0}/{1}'.format(self.__get_container_path(tenantid,
                                                              container_name),
                                    uuid.uuid4())

    def get_etag(self, data):
        etag_generator = hashlib.md5()
        for d in data:
            etag_generator.update(d)

        return etag_generator.hexdigest().upper()

    def get_file_etag(self, file_name):
        etag_generator = hashlib.md5()
        with open(file_name, 'rb') as input_data:
            for chunk in input_data:
                etag_generator.update(chunk)

        return etag_generator.hexdigest().upper()

    def add_tenant(self, tenantid):
        self.log_debug('Swift Service ({0}): Checking if Tenant {1} exists...'
                     .format(self.__id, tenantid))

        try:
            intTenantId = self.__model.has_tenant(tenantid)

        except SwiftUnknownTenantError:
            path = self.__get_tenant_path(tenantid)
            self.log_exception(
                'SwiftService ({0}): Adding Tenant {1} at path {2}'
                .format(self.__id, tenantid, path))
            intTenantId = self.__model.add_tenant(tenantid, path)

        if not os.path.exists(path):
            self.log_debug(
                'SwiftService ({0}): Creating path for Tenant {1} at {2}'
                .format(self.__id, tenantid, path))
            os.mkdir(path)

        return intTenantId

    def has_tenant(self, tenantid):
        try:
            intTenantId = self.__model.has_tenant(tenantid)

            tenant_info = self.__model.get_tenant(intTenantId)
            return os.path.exists(tenant_info['path'])

        except Exception:
            self.log_exception(
                'SwiftService ({0}): Unknown Tenant {1}'
                .format(self.__id, tenantid))
            return False

    def add_container(self, tenantid, container_name):
        self.log_debug('Swift Service ({0}): Checking for container\'s tenant '
                     '- {1}'
                     .format(self.__id, tenantid))

        intTenantId = None
        try:
            intTenantId = self.__model.has_tenant(tenantid)

        except SwiftUnknownTenantError:
            self.log_exception(
                'SwiftService ({0}): Adding Unknown Tenant {1}...'
                .format(self.__id, tenantid))
            intTenantId = self.add_tenant(tenantid)

        self.log_debug('Swift Service ({0}): Checking that container {2} exists '
                     'for tenant {1}'
                     .format(self.__id, tenantid, container_name))
        path = self.__get_container_path(tenantid, container_name)
        intContainerId = self.__model.add_container(intTenantId,
                                                    container_name,
                                                    path)

        if not os.path.exists(path):
            self.log_debug(
                'SwiftService ({0}): Adding Container {2} for Tenant {1} at '
                'path {3}'
                .format(self.__id, tenantid, container_name, path))
            os.mkdir(path)

        return (intTenantId, intContainerId)

    def has_container(self, tenantid, container_name):
        try:
            intTenantId = self.__model.has_tenant(tenantid)
            intContainerId = self.__model.has_container(intTenantId,
                                                        container_name)
            container_info = self.__model.get_container(intTenantId,
                                                        intContainerId)
            path = container_info['path']
            return os.path.exists(path)

        except Exception:
            self.log_exception(
                'SwiftService ({0}): Unknown Container {2} or Tenant {1}'
                .format(self.__id, tenantid, container_name))
            return False

    def get_container(self, tenantid, container_name):
        try:
            intTenantId = self.__model.has_tenant(tenantid)
            intContainerId = self.__model.has_container(intTenantId,
                                                        container_name)
            return (intTenantId, intContainerId)

        except Exception:
            self.log_exception(
                'SwiftService ({0}): Unknown Container {2} or Tenant {1}'
                .format(self.__id, tenantid, container_name))
            return (None, None)

    def has_object(self, tenantid, container_name, object_name):
        try:
            intTenantId = self.__model.has_tenant(tenantid)
            intContainerId = self.__model.has_container(intTenantId,
                                                        container_name)
            intObjectId = self.__model.has_object(intTenantId,
                                                  intContainerId,
                                                  object_name)
            object_info = self.__model.get_object(intTenantId,
                                                  intContainerId,
                                                  intObjectId)

            path = object_info['path']
            return os.path.exists(path)

        except Exception:
            self.log_exception(
                'Swift Service ({0}): Unknown Object {3}, Container {2}, or '
                'Tenant {1}'
                .format(self.__id, tenantid, container_name, object_name))
            return False

    def load_object_from_file(self, tenantid, container_name, object_name,
                              file_name, file_size=None,
                              allow_file_size_mismatch=False):
        self.log_debug('Swift Service ({0}): Checking that tenant {1} has '
                     'container {2}'
                     .format(tenantid, container_name, object_name))
        if not self.has_container(tenantid, container_name):
            self.add_container(tenantid, container_name)

        self.log_debug('Swift Service ({0}): Loading object {3} from file into '
                     'containter {2} for tenant {1}'
                     .format(self.__id, tenantid, container_name, object_name))
        metadata = CaseInsensitiveDict()
        metadata.update({
            'content-length': str(file_size) if file_size else str(
                os.path.getsize(file_name)),
            'content-type': 'application/binary',
            'etag': self.get_file_etag(file_name)
        })
        with open(file_name, 'rb') as content:
            self.store_object(tenantid, container_name, object_name, content,
                              metadata, file_size, allow_file_size_mismatch)

    def load_object(self, tenantid, container_name, object_name, content,
                    file_size=None, allow_file_size_mismatch=False):
        self.log_debug('Swift Service ({0}): Checking that tenant {1} has '
                     'container {2}'
                     .format(tenantid, container_name, object_name))
        if not self.has_container(tenantid, container_name):
            self.add_container(tenantid, container_name)

        self.log_debug('Swift Service ({0}): Loading object {3} from python '
                     'object into containter {2} for tenant {1}'
                     .format(self.__id, tenantid, container_name, object_name))

        metadata = CaseInsensitiveDict()
        metadata.update({
            'content-length': str(file_size) if file_size else str(
                len(content)),
            'content-type': 'application/binary',
            'etag': self.get_etag(content)
        })
        self.store_object(tenantid, container_name, object_name, content,
                          metadata, file_size, allow_file_size_mismatch)

    def update_object_etag(self, tenantid, container_name, object_name,
                           new_etag):
        path = self.__get_object_path(tenantid, container_name, object_name)
        if path in self.__metadata_information:
            self.__metadata_information[path]['etag'] = new_etag

    def store_or_update_custom_metadata(self, tenantid, container_name,
                                        object_name, metadata):
        self.log_debug('Swift Service ({0}): Storing custom metadata - {1}'
                     .format(self.__id, metadata))
        path = self.__get_object_path(tenantid, container_name, object_name)
        if path in self.__custom_metadata:
            self.log_debug('Swift Service ({0}): Updating existing custom '
                         'metadata {1} with {2}'
                         .format(self.__id,
                                 self.__custom_metadata[path],
                                 metadata))
            self.__custom_metadata[path].update(metadata)
            self.log_debug('Swift Service ({0}): updated existing custom '
                         'metadata {1}'
                         .format(self.__id, self.__custom_metadata[path]))
        else:
            self.log_debug('Swift Service ({0}): no existing custom metadata')
            self.__custom_metadata[path] = metadata
            self.log_debug('Swift Service ({0}): saved custom metadata {1}'
                         .format(self.__id, self.__custom_metadata[path]))

    def retrieve_custom_metadata(self, tenantid, container_name, object_name):
        custom_metadata = CaseInsensitiveDict()

        path = self.__get_object_path(tenantid, container_name, object_name)
        if path in self.__custom_metadata:
            custom_metadata.update(self.__custom_metadata[path])

        return custom_metadata

    def remove_custom_metadata(self, tenantid, container_name, object_name):
        custom_metadata = CaseInsensitiveDict()

        path = self.__get_object_path(tenantid, container_name, object_name)
        if path in self.__custom_metadata:
            del self.__custom_metadata[path]

    def store_object(self, tenantid, container_name, object_name, content,
                     metadata, file_size=None, allow_file_size_mismatch=False):
        if not self.has_container(tenantid, container_name):
            intTenantId, intContainerId = self.add_container(tenantid,
                                                             container_name)

        else:
            intTenantId, intContainerId = self.get_container(tenantid,
                                                             container_name)

        path = self.__get_object_path(tenantid, container_name, object_name)
        self.log_debug('Swift Service ({0}): Using path {1} for object '
                     '{2}/{3}:{4}'
                     .format(self.__id, path, tenantid, container_name,
                             object_name))

        self.__model.add_object(intTenantId,
                                intContainerId,
                                object_name,
                                path)

        self.log_debug('Swift Service ({0}): Added object to model'
                     .format(self.__id, path))

        with open(path, 'wb') as object_file:
            for c in content:
                object_file.write(c)

            object_file.flush()

        self.log_debug('Swift Service ({0}): object data stored'
                     .format(self.__id))

        for k, v in six.iteritems(metadata):
            self.log_debug('Swift Service ({0}): Storing Metadata[{1}] = {2}'
                         .format(self.__id, k, v))

        if file_size is None:
            file_size = os.path.getsize(path)

        self.log_debug('Swift Service ({0}): object has disk size of {1} bytes'
                     .format(self.__id, file_size))

        if int(metadata['content-length']) != file_size:
            self.log_debug('Swift Service ({0}): {1} != {2}. Object not stored '
                         'on disk properly'
                         .format(self.__id,
                                 metadata['content-length'],
                                 file_size))
            if not allow_file_size_mismatch:
                self.log_debug('Swift Service ({0}): File on disk must match '
                             'specified file size. ERROR!!!'
                             .format(self.__id))
                raise RuntimeError('Swift Service ({0}):'
                                   'Failed to store all bytes for the object'
                                   .format(self.__id))

            else:
                self.log_debug('Swift Service ({0}): File on disk may differ '
                             'specified file size.'
                             .format(self.__id))

        metadata['x-y-object-disk-path'] = path

        for k, v in six.iteritems(metadata):
            self.log_debug('Swift Service ({0}): Storing Metadata - {1} = {2}'
                         .format(self.__id, k, v))
        self.__metadata_information[path] = metadata
        self.log_debug('Swift Service ({0}): Metadata stored'
                     .format(self.__id))

    def retrieve_object(self, tenantid, container_name, object_name):
        if self.has_object(tenantid, container_name, object_name):
            metadata = CaseInsensitiveDict()
            path = self.__get_object_path(tenantid,
                                          container_name,
                                          object_name)
            if path in self.__metadata_information:
                metadata.update(self.__metadata_information[path])

            custom_metadata = self.retrieve_custom_metadata(tenantid,
                                                            container_name,
                                                            object_name)
            for k, v in six.iteritems(custom_metadata):
                self.log_debug('Swift Service ({0}): Custom Metadata[{1}] = '
                             '{2} with type {3}'
                             .format(self.__id, k, v, type(v)))
            metadata.update(custom_metadata)

            self.log_debug('Swift Service ({0}): Returning metadata - {1}'
                         .format(self.__id, metadata))

            self.log_debug('Swift Service ({0}): Metadata data length - {1}'
                         .format(self.__id, metadata['content-length']))

            data = None
            try:
                with open(path, 'rb') as data_input:
                    data = io.BytesIO(data_input.read())

                data.seek(0, os.SEEK_END)
                self.log_debug('Swift Service ({0}): Returning length - {1}'
                             .format(self.__id, data.tell()))
                data.seek(0, os.SEEK_SET)

            except Exception as ex:
                self.log_exception('Failed to read object from disk')
                data = None

            return (data,
                    metadata)

        else:
            self.log_debug('Swift Service ({0}): No object.'
                         .format(self.__id))
            return (None, None)

    def remove_object(self, tenantid, container_name, object_name):
        if self.has_object(tenantid, container_name, object_name):
            intTenantId, intContainerId = self.get_container(tenantid,
                                                             container_name)

            path = self.__get_object_path(tenantid,
                                          container_name,
                                          object_name)
            self.log_debug('Swift Service ({0}): Using path {1} for object '
                         '{2}/{3}:{4}'
                         .format(self.__id, path, tenantid, container_name,
                                 object_name))

            intTenantId = self.__model.has_tenant(tenantid)
            intContainerId = self.__model.has_container(intTenantId,
                                                        container_name)
            intObjectId = self.__model.has_object(intTenantId,
                                                  intContainerId,
                                                  object_name)
            self.log_debug('Swift Service ({0}): T: {1}, C: {2}, O: {3}'
                         .format(self.__id,
                                 intTenantId,
                                 intContainerId,
                                 intObjectId))

            self.__model.remove_object(intTenantId,
                                       intContainerId,
                                       intObjectId)

            self.log_debug('Swift Service ({0}): removed object from model'
                         .format(self.__id))

            os.remove(path)
            self.log_debug('Swift Service ({0}): removed object from disk'
                         .format(self.__id))

        else:
            self.log_debug('Swift Service ({0}): No object to remove'
                         .format(self.__id))

    def add_transaction(self, headers):
        headers['x-trans-id'] = str(uuid.uuid4())
        headers['date'] = str(datetime.datetime.utcnow())

    def get_object_handler(self, request, uri, headers):
        self.log_debug('Swift Service ({0}): Received GET request on {1}'
                     .format(self.__id, uri))

        self.add_transaction(headers)
        self.log_debug('Swift Service ({0}): Added transaction data to headers'
                     .format(self.__id))

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None:
            return (self, fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        self.log_debug('Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'
                     .format(self.__id, tenantid, container_name, object_name))

        try:
            data, metadata = self.retrieve_object(tenantid,
                                                  container_name,
                                                  object_name)
            self.log_debug('Swift Service ({0}): Retrieved object'
                         .format(self.__id))

        except Exception as ex:
            self.log_exception('Swift Service ({0}): Error while retrieving '
                             'object'
                             .format(self.__id))
            data = None
            metadata = None

        if metadata is not None:
            self.log_debug('Swift Service ({0}): Dumping metadata...'
                         .format(self.__id))
            for k, v in six.iteritems(metadata):
                self.log_debug('Swift Service ({0}): Returning Metadata[{1}] '
                             '= {2}'
                             .format(self.__id, k, v))

            self.log_debug('Swift Service ({0}): Metadata dump completed'
                         .format(self.__id))

        if data is None:
            self.log_debug('Swift Service ({0}): Did not find requested T/C:O '
                         'of {1}/{2}:{3}'
                         .format(self.__id,
                                 tenantid,
                                 container_name,
                                 object_name))
            return (404, headers, 'Not found')

        else:
            self.log_debug('Swift Service ({0}): Updating headers with '
                         'metadata information'
                         .format(self.__id))
            headers.update(metadata)

            for k, v in six.iteritems(headers):
                self.log_debug('Swift Service ({0}): Sending Header[{1}] = {2}'
                             .format(self.__id, k, v))

            self.log_debug('Swift Service ({0}): body has python type {1}'
                         .format(self.__id, str(type(data))))
            self.log_debug('Swift Service ({0}): Returning object'
                         .format(self.__id))

            if int(headers['content-length']) > 0:
                return (200, headers, data)

            else:
                return (204, headers, None)

    def put_object_handler(self, request, uri, headers):
        self.log_debug('Swift Service ({0}): Received PUT request on {1}'
                     .format(self.__id, uri))

        self.add_transaction(headers)
        self.log_debug('Swift Service ({0}): Added transaction data to headers'
                     .format(self.__id))

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None and \
                self.fail_error_code not in range(200, 299):
            return (self, fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        self.log_debug('Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'
                     .format(self.__id, tenantid, container_name, object_name))

        for k, v in six.iteritems(request.headers):
            self.log_debug('Swift Service ({0}): Received Header[{1}] = {2}'
                         .format(self.__id, k, v))

        if 'x-auth-token' not in request.headers:
            self.log_debug('Swift Service ({0}): Missing X-Auth-Token Header'
                         .format(self.__id))
            return (401, headers, 'Not Authorized')

        if 'etag' not in request.headers:
            self.log_debug('Swift Service ({0}): Missing ETAG Header'
                         .format(self.__id))
            return (400, headers, 'missing etag')

        metadata_headers = [
            'x-auth-token'
        ]

        self.log_debug('Swift Service ({0}): Filtering headers to store'
                     'relevant return headers as metadata'
                     .format(self.__id))
        metadata = CaseInsensitiveDict()
        for k, v in request.headers.items():
            if k.lower() not in metadata_headers:
                metadata[k] = v

        self.log_debug('Swift Service ({0}): Headers filtered.'
                     .format(self.__id))

        self.log_debug('Swift service ({0}): Body has type {1}'
                     .format(self.__id, type(request.body)))
        try:
            self.store_object(tenantid,
                              container_name,
                              object_name,
                              request.body,
                              metadata)
            self.log_debug('Swift Service ({0}): Object Stored'
                         .format(self.__id))

        except Exception as ex:
            self.log_exception('Swift Service ({0}): Failed to store object'
                             .format(self.__id))
            return (500, headers, 'Failed to store object')

        for k, v in six.iteritems(metadata):
            self.log_debug('Swift Service ({0}): Return Metadata[{1}] = {2}'
                         .format(self.__id, k, v))

        self.log_debug('Swift Service ({0}): Updating return headers...'
                     .format(self.__id))
        headers['etag'] = metadata['ETAG']
        self.log_debug('Swift Service ({0}): ETAG set'
                     .format(self.__id))

        headers['x-content-length'] = str(metadata['Content-Length'])

        self.log_debug('Swift Service ({0}): Return headers updated'
                     .format(self.__id))

        if self.fail_error_code:
            self.log_debug('Swift Service ({0}): Fail Mode enabled - '
                         'Returning Failure code {1}'
                         .format(self.__id, self.fail_error_code))
            return (self.fail_error_code, headers, '')

        else:
            self.log_debug('Swift Service ({0}): Returning success - 201'
                         .format(self.__id))
            return (201, headers, None)

    def head_object_handler(self, request, uri, headers):
        self.log_debug('Swift Service ({0}): Received HEAD request on {1}'
                     .format(self.__id, uri))

        self.add_transaction(headers)
        self.log_debug('Swift Service ({0}): Added transaction data to headers'
                     .format(self.__id))

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None:
            return (self, fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        self.log_debug('Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'
                     .format(self.__id, tenantid, container_name, object_name))

        try:
            chunker, metadata = self.retrieve_object(tenantid,
                                                     container_name,
                                                     object_name)
            self.log_debug('Swift Service ({0}): Retrieved object'
                         .format(self.__id))

        except Exception as ex:
            self.log_exception('Swift Service ({0}): Error retrieving object'
                             .format(self.__id))
            chunker = None,
            metadata = {}

        if chunker is None:
            self.log_debug('Swift Service ({0}): Did not find the object'
                         .format(self.__id))
            return (404, headers, 'Not found')

        else:
            self.log_debug('Swift Service ({0}): Found the object'
                         .format(self.__id))
            for k, v in six.iteritems(metadata):
                self.log_debug('Swift Service ({0}): Metadata[{1}] = {2} with '
                             'type {3}'
                             .format(self.__id, k, v, type(v)))

            headers.update(metadata)
            try:
                custom_metadata = self.retrieve_custom_metadata(tenantid,
                                                                container_name,
                                                                object_name)
                for k, v in six.iteritems(custom_metadata):
                    self.log_debug('Swift Service ({0}): Custom Metadata[{1}] '
                                 '= {2} with type {3}'
                                 .format(self.__id, k, v, type(v)))

                headers.update(custom_metadata)
            except:
                self.log_exception('Swift Service ({0}): Error retrieving '
                                 'custom metadata'
                                 .format(self.__id))

            return (204, headers, None)

    def delete_object_handler(self, request, uri, headers):
        self.log_debug('Swift Service ({0}): Received DELETE request on {1}'
                     .format(self.__id, uri))

        self.add_transaction(headers)
        self.log_debug('Swift Service ({0}): Added transaction data to headers'
                     .format(self.__id))

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None:
            return (self, fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        self.log_debug('Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'
                     .format(self.__id, tenantid, container_name, object_name))

        try:
            chunker, metadata = self.retrieve_object(tenantid,
                                                     container_name,
                                                     object_name)
            self.log_debug('Swift Service ({0}): Retrieved object'
                         .format(self.__id))

        except Exception as ex:
            self.log_exception('Swift Service ({0}): Error retrieving object'
                             .format(self.__id))
            chunker = None,
            metadata = {}

        if chunker is None:
            self.log_debug('Swift Service ({0}): Did not find the object'
                         .format(self.__id))
            return (404, headers, 'Not found')

        else:
            self.log_debug('Swift Service ({0}): Found the object'
                         .format(self.__id))

            try:
                self.remove_custom_metadata(tenantid,
                                            container_name,
                                            object_name)
                self.log_debug('Swift Service ({0}): Removed custom metadata'
                             .format(self.__id))

                self.remove_object(tenantid,
                                   container_name,
                                   object_name)
                self.log_debug('Swift Service ({0}): Removed object'
                             .format(self.__id))
                return (204, headers, None)

            except:
                return (500, headers, 'Internal Server Error')
