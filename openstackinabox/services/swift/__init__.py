"""
OpenStack Swift Services
"""
import datetime
import logging
import re
import uuid

import six
from stackinabox.services.service import StackInABoxService
from stackinabox.util.tools import CaseInsensitiveDict

from openstackinabox.services import base_service

from openstackinabox.models.swift.model import SwiftServiceModel
from openstackinabox.services.swift.storage import SwiftStorage


LOG = logging.getLogger(__name__)


class SwiftService(base_service.BaseService):

    # URL_REGEX = re.compile('\A\/(.+)\/(.+)\/(.+)\Z')
    word_match = '([\.%~#@!&\^\*\(\)\+=\`\'":;><?\w-]+)'
    URL_REGEX = re.compile('\A\/{0}\/{0}\/(.+\Z)'.format(word_match))

    @staticmethod
    def split_uri(uri):
        LOG.debug(
            'SwiftService: Attempting to split URL: {0} using regex '
            '{1}'.format(
                uri, SwiftService.URL_REGEX.pattern
            )
        )
        data = SwiftService.URL_REGEX.match(uri)
        if data:
            data_groups = data.groups()
            LOG.debug(
                'SwiftService: Split URL into {0} groups'.format(
                    len(data_groups)
                )
            )

            for dg in data_groups:
                LOG.debug(
                    'SwiftService: Split URL - group: {0}'.format(dg)
                )

            return (data_groups[0], data_groups[1], data_groups[2])

        LOG.debug('Swift Service: Failed to split url')
        return (None, None, None)

    @staticmethod
    def sanitize_name(name):
        if '\\' in name:
            LOG.debug(
                'Swift Service: Updating object name to replace "\" with " "'
            )
            name = name.replace('\\', ' ')

        if '/' in name:
            LOG.debug(
                'Swift Service: Updating object name to replace "/" with " "'
            )
            name = name.replace('/', ' ')

        return name

    def __init__(self):
        super(SwiftService, self).__init__('swift/v1.0')
        self.__id = uuid.uuid4()
        self.__model = SwiftServiceModel()
        self.__storage = SwiftStorage(self.__id, self.__model)
        self.__metadata_information = {}
        self.__custom_metadata = {}
        self.fail_auth = False
        self.fail_error_code = None

    @property
    def storage(self):
        return self.__storage

    def do_register_object(self, tenantid, container_name, object_name):
        uri = '/{0}/{1}/{2}'.format(
            tenantid,
            container_name,
            object_name
        )
        LOG.debug(
            'SwiftService ({0}): Registering Object Service for '
            'T/C:O - {1}/{2}: {3}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )
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

    def add_transaction(self, headers):
        headers['x-trans-id'] = str(uuid.uuid4())
        headers['date'] = str(datetime.datetime.utcnow())

    def get_object_handler(self, request, uri, headers):
        LOG.debug(
            'Swift Service ({0}): Received GET request on {1}'.format(
                self.__id, uri
            )
        )

        self.add_transaction(headers)
        LOG.debug(
            'Swift Service ({0}): Added transaction data to headers'.format(
                self.__id
            )
        )

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None:
            return (self, self.fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        LOG.debug(
            'Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )

        try:
            data, metadata = self.storage.retrieve_object(
                tenantid,
                container_name,
                object_name
            )
            LOG.debug(
                'Swift Service ({0}): Retrieved object'.format(self.__id)
            )

        except Exception as ex:
            LOG.exception(
                'Swift Service ({0}): Error while retrieving object'.format(
                    self.__id
                )
            )
            data = None
            metadata = None

        if metadata is not None:
            LOG.debug(
                'Swift Service ({0}): Dumping metadata...'.format(self.__id)
            )
            for k, v in six.iteritems(metadata):
                LOG.debug(
                    'Swift Service ({0}): Returning Metadata[{1}] = {2}'
                    ''.format(
                        self.__id, k, v
                    )
                )

            LOG.debug(
                'Swift Service ({0}): Metadata dump completed'.format(
                    self.__id
                )
            )

        if data is None:
            LOG.debug(
                'Swift Service ({0}): Did not find requested T/C:O of '
                '{1}/{2}:{3}'.format(
                    self.__id,
                    tenantid,
                    container_name,
                    object_name
                )
            )
            return (404, headers, 'Not found')

        else:
            LOG.debug(
                'Swift Service ({0}): Updating headers with metadata '
                'information'.format(self.__id)
            )
            headers.update(metadata)

            for k, v in six.iteritems(headers):
                LOG.debug(
                    'Swift Service ({0}): Sending Header[{1}] = {2}'.format(
                        self.__id, k, v
                    )
                )

            LOG.debug(
                'Swift Service ({0}): body has python type {1}'.format(
                    self.__id, str(type(data))
                )
            )
            LOG.debug(
                'Swift Service ({0}): Returning object'.format(self.__id)
            )

            if int(headers['content-length']) > 0:
                return (200, headers, data)

            else:
                return (204, headers, None)

    def put_object_handler(self, request, uri, headers):
        LOG.debug(
            'Swift Service ({0}): Received PUT request on {1}'.format(
                self.__id, uri
            )
        )

        self.add_transaction(headers)
        LOG.debug(
            'Swift Service ({0}): Added transaction data to headers'.format(
                self.__id
            )
        )

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif (
            self.fail_error_code is not None and
            self.fail_error_code not in range(200, 299)
        ):
            return (self, self.fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        LOG.debug(
            'Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )

        for k, v in six.iteritems(request.headers):
            LOG.debug(
                'Swift Service ({0}): Received Header[{1}] = {2}'.format(
                    self.__id, k, v
                )
            )

        if 'x-auth-token' not in request.headers:
            LOG.debug(
                'Swift Service ({0}): Missing X-Auth-Token Header'.format(
                    self.__id
                )
            )
            return (401, headers, 'Not Authorized')

        if 'etag' not in request.headers:
            LOG.debug(
                'Swift Service ({0}): Missing ETAG Header'.format(
                    self.__id
                )
            )
            return (400, headers, 'missing etag')

        metadata_headers = [
            'x-auth-token'
        ]

        LOG.debug(
            'Swift Service ({0}): Filtering headers to store'
            'relevant return headers as metadata'.format(self.__id)
        )
        metadata = CaseInsensitiveDict()
        for k, v in request.headers.items():
            if k.lower() not in metadata_headers:
                metadata[k] = v

        LOG.debug(
            'Swift Service ({0}): Headers filtered.'.format(self.__id)
        )

        LOG.debug(
            'Swift service ({0}): Body has type {1}'.format(
                self.__id, type(request.body)
            )
        )
        try:
            self.storage.store_object(
                tenantid,
                container_name,
                object_name,
                request.body,
                metadata
            )
            LOG.debug(
                'Swift Service ({0}): Object Stored'.format(self.__id)
            )

        except Exception as ex:
            LOG.exception(
                'Swift Service ({0}): Failed to store object'.format(self.__id)
            )
            return (500, headers, 'Failed to store object')

        for k, v in six.iteritems(metadata):
            LOG.debug(
                'Swift Service ({0}): Return Metadata[{1}] = {2}'.format(
                    self.__id, k, v
                )
            )

        LOG.debug(
            'Swift Service ({0}): Updating return headers...'.format(self.__id)
        )
        headers['etag'] = metadata['ETAG']
        LOG.debug('Swift Service ({0}): ETAG set'.format(self.__id))

        headers['x-content-length'] = str(metadata['Content-Length'])

        LOG.debug(
            'Swift Service ({0}): Return headers updated'.format(self.__id)
        )

        if self.fail_error_code:
            LOG.debug(
                'Swift Service ({0}): Fail Mode enabled - Returning Failure '
                'code {1}'.format(
                    self.__id, self.fail_error_code
                )
            )
            return (self.fail_error_code, headers, '')

        else:
            LOG.debug(
                'Swift Service ({0}): Returning success - 201'.format(
                    self.__id
                )
            )
            return (201, headers, None)

    def head_object_handler(self, request, uri, headers):
        LOG.debug(
            'Swift Service ({0}): Received HEAD request on {1}'.format(
                self.__id, uri
            )
        )

        self.add_transaction(headers)
        LOG.debug(
            'Swift Service ({0}): Added transaction data to headers'.format(
                self.__id
            )
        )

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None:
            return (self, self.fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        LOG.debug(
            'Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )

        try:
            chunker, metadata = self.storage.retrieve_object(
                tenantid,
                container_name,
                object_name
            )
            LOG.debug(
                'Swift Service ({0}): Retrieved object'.format(self.__id)
            )

        except Exception as ex:
            LOG.exception(
                'Swift Service ({0}): Error retrieving object'.format(
                    self.__id
                )
            )
            chunker = None,
            metadata = {}

        if chunker is None:
            LOG.debug(
                'Swift Service ({0}): Did not find the object'.format(
                    self.__id
                )
            )
            return (404, headers, 'Not found')

        else:
            LOG.debug(
                'Swift Service ({0}): Found the object'.format(self.__id)
            )
            for k, v in six.iteritems(metadata):
                LOG.debug(
                    'Swift Service ({0}): Metadata[{1}] = {2} with type '
                    '{3}'.format(
                        self.__id, k, v, type(v)
                    )
                )

            headers.update(metadata)
            try:
                custom_metadata = self.retrieve_custom_metadata(
                    tenantid,
                    container_name,
                    object_name
                )
                for k, v in six.iteritems(custom_metadata):
                    LOG.debug(
                        'Swift Service ({0}): Custom Metadata[{1}] = {2} '
                        'with type {3}'.format(
                            self.__id, k, v, type(v)
                        )
                    )

                headers.update(custom_metadata)
            except:
                LOG.exception(
                    'Swift Service ({0}): Error retrieving custom '
                    'metadata'.format(
                        self.__id
                    )
                )

            return (204, headers, None)

    def delete_object_handler(self, request, uri, headers):
        LOG.debug(
            'Swift Service ({0}): Received DELETE request on {1}'.format(
                self.__id, uri
            )
        )

        self.add_transaction(headers)
        LOG.debug(
            'Swift Service ({0}): Added transaction data to headers'.format(
                self.__id
            )
        )

        if self.fail_auth:
            return (401, headers, 'Unauthorized')

        elif self.fail_error_code is not None:
            return (self, self.fail_error_code, headers, 'mock error')

        tenantid, container_name, object_name = SwiftService.split_uri(uri)
        LOG.debug(
            'Swift Service ({0}): Requested T/C:O on {1}/{2}:{3}'.format(
                self.__id, tenantid, container_name, object_name
            )
        )

        try:
            chunker, metadata = self.storage.retrieve_object(
                tenantid,
                container_name,
                object_name
            )
            LOG.debug(
                'Swift Service ({0}): Retrieved object'.format(self.__id)
            )

        except Exception as ex:
            LOG.exception(
                'Swift Service ({0}): Error retrieving object'.format(
                    self.__id
                )
            )
            chunker = None,

        if chunker is None:
            LOG.debug(
                'Swift Service ({0}): Did not find the object'.format(
                    self.__id
                )
            )
            return (404, headers, 'Not found')

        else:
            LOG.debug(
                'Swift Service ({0}): Found the object'.format(self.__id)
            )

            try:
                self.remove_custom_metadata(tenantid,
                                            container_name,
                                            object_name)
                LOG.debug(
                    'Swift Service ({0}): Removed custom metadata'.format(
                        self.__id
                    )
                )

                self.storage.remove_object(
                    tenantid,
                    container_name,
                    object_name
                )
                LOG.debug(
                    'Swift Service ({0}): Removed object'.format(self.__id)
                )
                return (204, headers, None)

            except:
                return (500, headers, 'Internal Server Error')
