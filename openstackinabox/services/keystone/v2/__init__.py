"""
OpenStack Keystone v2 Service
"""
import json
import re
import uuid

import six

from openstackinabox.models.keystone import KeystoneModel
from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2.tenants import (
    KeystoneV2ServiceTenants
)
from openstackinabox.services.keystone.v2.users import (
    KeystoneV2ServiceUsers
)

class KeystoneV2Errors(Exception):
    pass


class KeystoneV2AuthError(Exception):
    pass


class KeystoneV2AuthForbiddenError(KeystoneV2AuthError):
    pass


class KeystoneV2AuthUnauthorizedError(KeystoneV2AuthError):
    pass


class KeystoneV2Service(BaseService):

    def __init__(self):
        super(KeystoneV2Service, self).__init__('keystone/v2.0')
        self.log_info('initializing keystone v2.0 services...')
        self.__model = KeystoneModel()

        self.__subservices = [
            KeystoneV2ServiceTenants(self),
            KeystoneV2ServiceUsers(self)
        ]

        self.add_subservices(self.__subservices)

        self.log_info('initialized')

    def get_model(self):
        return self.__model

    def set_model(self, value):
        if isinstance(value, KeystoneModel):
            self.__model = value
        else:
            raise TypeError('model is not an instance of KeystoneModel')

    def helper_validate_token(self, request_headers,
                              enforce_admin, service_admin):
        if 'x-auth-token' not in request_headers:
            raise KeystoneV2AuthForbiddenError('no auth token')

        try:
            auth_token = request_headers['x-auth-token']
            user_data = None
            if service_admin:
                user_data = self.model.validate_token_service_admin(auth_token)

            elif enforce_admin:
                user_data = self.model.validate_token_admin(auth_token)

            else:
                user_data = self.model.validate_token(auth_token)

            self.log_debug('token {0} maps to tenant {1} and userid {2}'
                           .format(auth_token,
                                   user_data['tenantid'],
                                   user_data['userid']))
        except Exception as ex:
            raise KeystoneV2AuthUnauthorizedError(
                'invalid or expired auth token')

        return user_data

    def helper_authenticate(self, request_headers, headers,
                            enforce_admin, service_admin):

        try:
            user_data = self.helper_validate_token(request_headers,
                                                   enforce_admin,
                                                   service_admin)

        except KeystoneV2AuthForbiddenError:
            self.log_exception('no token')
            return (403, headers, 'Forbidden')

        except KeystoneV2AuthUnauthorizedError:
            self.log_exception('invalid or expired token')
            return (401, headers, 'Not Authorized')

        return user_data
