import json
import re

from openstackinabox.services.cinder.v1 import base


class CinderV1Volumes(base.CinderV1ServiceBase):

    # Note: OpenStackInABox's Keystone Service doesn't have support
    #   right now for inserting the tenant-id into the URL when
    #   generating the service catalog. So the service URL here
    #   can't search for it
    ALL_VOLUMES = re.compile(r'^/volumes$')
    ALL_VOLUMES_DETAILED = re.compile(r'^/volumes/detail$')
    SPECIFIC_VOLUME = re.compile(r'^/volumes/[\w-]+$')

    def __init__(self, model, keystone_service):
        super(CinderV1Volumes, self).__init__(
            keystone_service,
            'cinder/v1/volumes'
        )
        self.model = model

        self.__handlers = [
            {
                'verb': base.CinderV1ServiceBase.POST,
                'path': self.ALL_VOLUMES,
                'handler': CinderV1Volumes.handle_create_volume
            },
            {
                'verb': base.CinderV1ServiceBase.GET,
                'path': self.ALL_VOLUMES,
                'handler': CinderV1Volumes.handle_retrieve_volumes
            },
            {
                'verb': base.CinderV1ServiceBase.PUT,
                'path': self.SPECIFIC_VOLUME,
                'handler': CinderV1Volumes.handle_update_volume
            },
            {
                'verb': base.CinderV1ServiceBase.DELETE,
                'path': self.SPECIFIC_VOLUME,
                'handler': CinderV1Volumes.handle_delete_volume
            },
            {
                'verb': base.CinderV1ServiceBase.GET,
                'path': self.SPECIFIC_VOLUME,
                'handler': CinderV1Volumes.get_subroute
                # NOTE: There is a conflict between SPECIFIC_VOLUME and
                #   ALL_VOLUMES when it comes to the GET verb. Therefore
                #   a special sub-router is required to propery direct
                #   the request as StackInABox doesn't allow two registrations
                #   on the same VERB where the path may match.
            }
        ]

        for handler in self.__handlers:
            self.register(
                handler['verb'],
                handler['path'],
                handler['handler']
            )

    def get_subroute(self, request, uri, headers):
        uri_parts = uri.split('/')
        if uri_parts[-1] == 'detail':
            return self.handle_retrieve_volumes_detailed(
                request, uri, headers
            )
        else:
            return self.handle_retrieve_volume_details(
                request, uri, headers
            )

    def handle_create_volume(self, request, uri, headers):
        # https://developer.rackspace.com/docs/cloud-block-storage/v1/
        #   api-reference/cbs-volumes-operations/#create-a-volume
        return (500, headers, 'Not yet implemented')

    def handle_retrieve_volumes(self, request, uri, headers):
        # https://developer.rackspace.com/docs/cloud-block-storage/v1/
        #   api-reference/cbs-volumes-operations/#retrieve-volumes
        return (500, headers, 'Not yet implemented')

    def handle_retrieve_volumes_detailed(self, request, uri, headers):
        # https://developer.rackspace.com/docs/cloud-block-storage/v1/
        #   api-reference/cbs-volumes-operations/#retrieve-volumes-detailed
        return (500, headers, 'Not yet implemented')

    def handle_update_volume(self, request, uri, headers):
        # https://developer.rackspace.com/docs/cloud-block-storage/v1/
        #   api-reference/cbs-volumes-operations/#update-a-volume
        return (500, headers, 'Not yet implemented')

    def handle_delete_volume(self, request, uri, headers):
        # https://developer.rackspace.com/docs/cloud-block-storage/v1/
        #   api-reference/cbs-volumes-operations/#delete-a-volume
        return (500, headers, 'Not yet implemented')

    def handle_retrieve_volume_details(self, request, uri, headers):
        # https://developer.rackspace.com/docs/cloud-block-storage/v1/
        #   api-reference/cbs-volumes-operations/#retrieve-details-for-a-volume
        req_headers = request.headers
        self.log_request(uri, request)

        # Validate the token in the request headers
        # - if it's invalid for some reason a tuple is returned
        # - if all is good, then a dict with the user information is returned
        user_data = self.helper_authenticate(
            req_headers, headers, False, False
        )

        # user_data will be a tuple in the case of 401/403 errors
        if isinstance(user_data, tuple):
            return user_data

        # volume id in the URI, nothing in the body
        result = self.SPECIFIC_VOLUME.match(uri)
        if result and not uri.split('/')[-1].startswith('_'):
            volume_id = result.group(0)

            # TODO: Mapping Tenant-ID in URL per OpenStack API norms
            # OpenStackInABox Keystone Service doesn't support the insert
            # of the tenant-id into the URL so the URL can't be used to
            # validate the tenant-id of the request.
            #
            # tenant_id = result.group(0)
            # volume_id = result.group(1)
            # if tenant_id != user_data['tenantid']:
            #    return (400, headers, 'Invalid client request')

            # technically the data should be looked up in the CinderModel
            # and a result returned accordingly; but right now the goal
            # is a very specific test so for MVP just return the result
            response_body = {
                'volume': {
                    'attachments': [],
                    'availability_zone': 'nova',
                    'bootable': 'false',
                    'created_at': '',
                    'display_description': 'clone in error state',
                    'display_name': 'clone_test',
                    'id': volume_id,
                    'image_id': None,
                    'metadata': {},
                    'size': 100,
                    'snapshot_id': None,
                    'source_volid': volume_id,  # self-referential
                    'status': 'error',
                    'volume_type': 'SATA',
                }
            }

            return (200, headers, json.dumps(response_body))

        else:
            return (400, headers, 'Invalid client request')
