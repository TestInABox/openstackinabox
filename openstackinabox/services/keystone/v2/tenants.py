"""
Openstack Keystone v2 Service - Tenants
"""
import json
import re

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.base_subservice import BaseSubService


class KeystoneV2ServiceTenants(BaseSubService):

    PATH = '/tenants'
    ROUTE_REGEX = re.compile('^{0}'.format(PATH))
    PATH_REGEX = re.compile('^{0}$'.format(PATH))

    def __init__(self, parent):
        super(KeystoneV2ServiceTenants, self).__init__('tenants', parent)

        self.register(BaseService.GET,
                      KeystoneV2ServiceTenants.PATH_REGEX,
                      KeystoneV2ServiceTenants.handle_list_tenants)

    def get_route_regex(self):
        return KeystoneV2ServiceTenants.ROUTE_REGEX

    def handle_list_tenants(self, request, uri, headers):
        '''
        200, 203 -> OK
        400 -> Bad Request: one or more required parameters
                            are missing or invalid
        401 -> not authorized
        403 -> forbidden (no permission)
        404 -> Not found
        405 -> Invalid Method
        413 -> Over Limit - too many items requested
        503 -> Service Fault
        '''
        self.log_request(uri, request)
        req_headers = request.headers

        user_data = self.get_root().helper_authenticate(req_headers,
                                                        headers,
                                                        True,
                                                        True)
        if isinstance(user_data, tuple):
            return user_data

        """
        Body on success:
        body = {
            'tenants' : [ {'id': 01234,
                           'name': 'bob',
                           'description': 'joe bob',
                           'enabled': True }]
            'tenants_links': []
        }
        """
        response_body = {
            'tenants': [tenant_info
                        for tenant_info in
                        self.model.get_tenants()],
            'tenants_links': []
        }
        return (200, headers, json.dumps(response_body))
