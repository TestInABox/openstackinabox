from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2.exceptions import *


class KeystoneV2ServiceBase(BaseService):

    def __init__(self, *args, **kwargs):
        super(KeystoneV2ServiceBase, self).__init__(*args, **kwargs)

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
