import re

from openstackinabox.models.keystone import KeystoneModel
from openstackinabox.services.base_service import BaseService
from openstackinabox.services.keystone.v2 import exceptions


class KeystoneV2ServiceBase(BaseService):

    # USER_ID_PATH_REGEX = re.compile('^\/users\/[a-zA-Z]+[\w\.@-]*$')
    USER_ID_REGEX = '([0-9]+)'
    USER_ID_PATH_REGEX = re.compile('^\/users\/{0}$'
                                    .format(USER_ID_REGEX))
    USER_ID_KSADM_CREDENTIAL_PATH_REGEX = re.compile(
        '^\/users\/{0}/OS-KSADM/credentials$'
        .format(USER_ID_REGEX))

    @staticmethod
    def get_user_id_from_path(uri_path):
        uri_matcher = None

        regexes = [
            KeystoneV2ServiceBase.USER_ID_PATH_REGEX,
            KeystoneV2ServiceBase.USER_ID_KSADM_CREDENTIAL_PATH_REGEX,
        ]

        for r in regexes:
            uri_matcher = r.match(uri_path)
            if uri_matcher is not None:
                break

        userid = uri_matcher.groups()[0]
        return userid

    def __init__(self, *args, **kwargs):
        super(KeystoneV2ServiceBase, self).__init__(*args, **kwargs)
        self.__model = None

    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, value):
        if isinstance(value, KeystoneModel):
            self.__model = value
        else:
            raise TypeError('model is not an instance of KeystoneModel')

    def helper_validate_token(self, request_headers,
                              enforce_admin, service_admin):
        if 'x-auth-token' not in request_headers:
            raise exceptions.KeystoneV2AuthForbiddenError('no auth token')

        try:
            auth_token = request_headers['x-auth-token']
            user_data = None
            self.log_debug('Service Admin Required: {0}'.format(service_admin))
            self.log_debug('Enforce Admin Required: {0}'.format(enforce_admin))

            if service_admin:
                user_data = self.model.validate_token_service_admin(auth_token)

            elif enforce_admin:
                user_data = self.model.validate_token_admin(auth_token)

            else:
                user_data = self.model.tokens.validate_token(auth_token)

            self.log_debug(
                'token {0} maps to tenant {1} and userid {2}'.format(
                    auth_token,
                    user_data['tenantid'],
                    user_data['userid']
                )
            )
        except Exception as ex:
            self.log_exception('invalid or expired auth token')
            raise exceptions.KeystoneV2AuthUnauthorizedError(
                'invalid or expired auth token'
            )

        return user_data

    def helper_authenticate(self, request_headers, headers,
                            enforce_admin, service_admin):

        try:
            user_data = self.helper_validate_token(
                request_headers,
                enforce_admin,
                service_admin
            )

        except exceptions.KeystoneV2AuthForbiddenError:
            self.log_exception('no token')
            return (403, headers, 'Forbidden')

        except exceptions.KeystoneV2AuthUnauthorizedError:
            self.log_exception('invalid or expired token')
            return (401, headers, 'Not Authorized')

        return user_data
