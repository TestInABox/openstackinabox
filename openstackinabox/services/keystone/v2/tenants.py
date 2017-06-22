import json

from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2.base import KeystoneV2ServiceBase


class KeystoneV2ServiceTenants(KeystoneV2ServiceBase):

    def __init__(self, model):
        super(KeystoneV2ServiceTenants, self).__init__('keystone/v2.0/tenants')
        self.model = model

        self.register(
            BaseService.GET,
            '/tenants',
            KeystoneV2ServiceTenants.handle_listing
        )

    def handle_listing(self, request, uri, headers):
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

        user_data = self.helper_authenticate(req_headers, headers, True, True)
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
            'tenants': [
                tenant_info
                for tenant_info in
                self.model.tenants.get()
            ],
            'tenants_links': []
        }
        return (200, headers, json.dumps(response_body))
